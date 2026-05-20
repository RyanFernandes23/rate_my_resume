# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Header, Response, Request
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
from app.db import settings, service_supabase, get_client
from gotrue.errors import AuthApiError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse
    expires_in: int


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.replace("Bearer ", "")
    
    try:
        # Use a fresh client to avoid session pollution
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


@router.post("/register", response_model=Token)
async def register(user: UserCreate, response: Response):
    """Register user and return access/refresh tokens"""
    try:
        user_metadata = {}
        if user.name:
            user_metadata["name"] = user.name

        # Use a fresh client to avoid polluting the global service client
        auth_client = get_client(use_service_key=True)
        
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
        else:
            try:
                signin_response = auth_client.auth.sign_in_with_password(
                    {"email": user.email, "password": user.password}
                )
                access_token = signin_response.session.access_token
                refresh_token = signin_response.session.refresh_token
                expires_in = signin_response.session.expires_in or 3600
            except Exception as e:
                access_token = ""
                refresh_token = ""
                expires_in = 0

        user_id = auth_response.user.id
        user_email = auth_response.user.email or user.email

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse(id=user_id, email=user_email, name=user.name),
            expires_in=expires_in,
        )
        
    except AuthApiError as e:
        logger.error(f"Supabase auth error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=400, detail="Registration failed")


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, response: Response):
    """Login user and return access/refresh tokens"""
    try:
        # Use a fresh client to avoid polluting the global service client
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

        return Token(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            user=UserResponse(id=user.id, email=user.email, name=name),
            expires_in=session.expires_in or 3600,
        )
        
    except AuthApiError as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token_body: dict, response: Response):
    """Refresh access token using refresh token"""
    try:
        refresh_token_str = refresh_token_body.get("refresh_token")
        if not refresh_token_str:
            raise HTTPException(status_code=400, detail="Refresh token required")

        # Use a fresh client to avoid polluting the global service client
        auth_client = get_client(use_service_key=True)
        auth_response = auth_client.auth.refresh_session(refresh_token_str)
        
        if not auth_response.session:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user = auth_response.user
        session = auth_response.session
        user_metadata = user.user_metadata or {}

        return Token(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_type="bearer",
            user=UserResponse(id=user.id, email=user.email, name=user_metadata.get("name")),
            expires_in=session.expires_in or 3600,
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user"""
    try:
        # Use a fresh client to avoid session pollution
        auth_client = get_client(use_service_key=True)
        auth_client.auth.sign_out()
    except Exception as e:
        logger.error(f"Logout error: {e}")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email", ""),
        name=current_user.get("name"),
    )