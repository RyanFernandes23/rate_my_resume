# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import logging
from app.db import settings, get_client
from app.lib.cookie_service import CookieService, get_supabase_session_token
from gotrue.errors import AuthApiError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

from app.rate_limit import limiter


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


def _get_cookie_service() -> CookieService:
    return CookieService(secure=settings.cookie_secure)


async def get_current_user(request: Request) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )

    cookie_service = _get_cookie_service()
    token = cookie_service.get_access_token(request)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
    if not token:
        token = get_supabase_session_token(request, settings.supabase_url)
    if not token:
        raise credentials_exception

    try:
        auth_client = get_client(use_service_key=True)
        user_response = auth_client.auth.get_user(token)

        if not user_response.user:
            logger.warning("[GET_USER] No user found for token")
            raise credentials_exception

        user = user_response.user
        user_metadata = user.user_metadata or {}

        return {
            "id": user.id,
            "email": user.email,
            "name": user_metadata.get("name"),
        }

    except Exception as e:
        logger.warning(f"[GET_USER] Error: {type(e).__name__}: {e}")
        raise credentials_exception


@router.post("/register", response_model=AuthResponse)
@limiter.limit("5/hour")
async def register(request: Request, user: UserCreate, response: Response):
    """Register user and return user info. Auth tokens are set as HttpOnly cookies."""
    try:
        user_metadata = {}
        if user.name:
            user_metadata["name"] = user.name

        auth_client = get_client(use_service_key=True)

        resp = auth_client.auth.admin._http_client.get(
            f"{auth_client.auth.admin._url}/admin/users",
            params={"filter": user.email, "per_page": 1},
            headers=auth_client.auth.admin._headers,
        )
        existing = resp.json().get("users", [])
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please sign in instead."
            )

        auth_response = auth_client.auth.sign_up(
            {
                "email": user.email,
                "password": user.password,
                "options": {"data": user_metadata},
            }
        )

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Registration failed")

        if auth_response.session:
            access_token = auth_response.session.access_token
            refresh_token = auth_response.session.refresh_token
            expires_in = auth_response.session.expires_in or 3600

            cookie_service = _get_cookie_service()
            cookie_service.set_auth_cookies(response, access_token, refresh_token, expires_in)

            return AuthResponse(
                user=UserResponse(id=auth_response.user.id, email=auth_response.user.email or user.email, name=user.name),
            )

        raise HTTPException(
            status_code=202,
            detail="Please confirm your email address. A confirmation link has been sent to your email."
        )

    except AuthApiError as e:
        logger.error(f"Supabase auth error during registration: {e}")
        error_str = str(e)

        if "already registered" in error_str.lower():
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please sign in instead."
            )

        # Pass through the actual Supabase message for other errors
        # (e.g. invalid email, rate limited, etc.)
        raise HTTPException(status_code=400, detail=error_str)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, login_data: LoginRequest, response: Response):
    """Login user and return user info. Auth tokens are set as HttpOnly cookies."""
    try:
        auth_client = get_client(use_service_key=True)

        auth_response = auth_client.auth.sign_in_with_password(
            {
                "email": login_data.email,
                "password": login_data.password,
            }
        )

        if not auth_response.user or not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = auth_response.user
        session = auth_response.session

        user_metadata = user.user_metadata or {}
        name = user_metadata.get("name")

        cookie_service = _get_cookie_service()
        cookie_service.set_auth_cookies(
            response, session.access_token, session.refresh_token, session.expires_in or 3600
        )

        return AuthResponse(
            user=UserResponse(id=user.id, email=user.email, name=name),
        )

    except AuthApiError as e:
        logger.error(f"Supabase auth error during login: {e}")
        error_str = str(e).lower()

        if "email not confirmed" in error_str:
            raise HTTPException(
                status_code=401,
                detail="Please confirm your email before signing in"
            )

        if "invalid login credentials" in error_str or "invalid grant" in error_str:
            # Distinguish user-not-found from wrong-password
            try:
                user_list = auth_client.auth.admin.list_users(
                    filter=login_data.email, per_page=1
                )
                user_exists = len(user_list.users) > 0
            except Exception:
                user_exists = None

            if user_exists is False:
                raise HTTPException(
                    status_code=404,
                    detail="No account found with this email address"
                )

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        raise HTTPException(status_code=401, detail="Login failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh", response_model=AuthResponse)
@limiter.limit("10/minute")
async def refresh_token(request: Request, response: Response, body: Optional[RefreshRequest] = None):
    """Refresh access token. New auth tokens are set as HttpOnly cookies."""
    try:
        cookie_service = _get_cookie_service()
        refresh_token_str = cookie_service.get_refresh_token(request)

        if not refresh_token_str and body and body.refresh_token:
            refresh_token_str = body.refresh_token

        if not refresh_token_str:
            raise HTTPException(status_code=400, detail="Refresh token missing")

        auth_client = get_client(use_service_key=True)
        auth_response = auth_client.auth.refresh_session(refresh_token_str)

        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user = auth_response.user
        session = auth_response.session
        user_metadata = user.user_metadata or {}

        cookie_service.set_auth_cookies(
            response, session.access_token, session.refresh_token, session.expires_in or 3600
        )

        return AuthResponse(
            user=UserResponse(id=user.id, email=user.email, name=user_metadata.get("name")),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.post("/logout")
async def logout(response: Response, current_user: dict = Depends(get_current_user)):
    """Logout user"""
    try:
        auth_client = get_client(use_service_key=True)
        auth_client.auth.sign_out()
    except Exception as e:
        logger.error(f"Logout error: {e}")

    cookie_service = _get_cookie_service()
    cookie_service.clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email", ""),
        name=current_user.get("name"),
    )
