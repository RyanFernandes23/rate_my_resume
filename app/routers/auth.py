# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from pydantic import BaseModel
from typing import Optional
import logging
from app.db import settings, get_client
from app.lib.cookie_service import CookieService, get_supabase_session_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class AuthResponse(BaseModel):
    user: UserResponse


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


@router.post("/refresh", response_model=AuthResponse)
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
