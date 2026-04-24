# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Header, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from typing import Optional
import os
import logging
from app.db import settings, service_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() in ("true", "1", "yes")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", None)


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class SupabaseTokenRequest(BaseModel):
    user_id: str
    email: str
    name: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    expires_in: int = 900


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    logger.info(f"[CREATE_ACCESS] Using secret: {settings.supabase_jwt_secret[:15]}...")
    encoded_jwt = jwt.encode(to_encode, settings.supabase_jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire.timestamp(), "type": "refresh"})
    logger.info(f"[CREATE_REFRESH] Using secret: {settings.supabase_jwt_secret[:15]}...")
    encoded_jwt = jwt.encode(to_encode, settings.supabase_jwt_secret, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[dict]:
    try:
        logger.info(f"[VERIFY] Starting verification with secret: {settings.supabase_jwt_secret[:15]}...")
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=[ALGORITHM])

        if payload.get("type") != "refresh":
            logger.warning("[REFRESH] Token type mismatch")
            return None

        exp = payload.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            logger.warning("[REFRESH] Token expired")
            return None

        logger.info(f"[REFRESH] Token valid for user: {payload.get('sub')}")
        return payload
    except JWTError as e:
        logger.warning(f"[REFRESH] JWT Error: {e}")
        return None
    except Exception as e:
        logger.warning(f"[REFRESH] Unexpected error: {e}")
        return None


async def get_current_user(authorization: str = Header(...)) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.replace("Bearer ", "")
    logger.info(f"[GET_USER] Token received: {token[:30]}...")
    logger.info(f"[GET_USER] Using secret: {settings.supabase_jwt_secret[:15]}...")

    try:
        payload = jwt.decode(
            token, settings.supabase_jwt_secret, algorithms=[ALGORITHM]
        )
        logger.info(f"[GET_USER] Decoded payload: {payload}")
        
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("[GET_USER] No sub in payload")
            raise credentials_exception

        user_email = payload.get("email", "")

        logger.info(f"[GET_USER] Fetching user from Supabase: {user_id}")
        user_response = service_supabase.auth.admin.get_user_by_id(user_id)
        if not user_response.user:
            raise HTTPException(status_code=404, detail="User not found")

        user_metadata = user_response.user.user_metadata or {}
        name = user_metadata.get("name")

        return {
            "id": user_id,
            "email": user_email,
            "name": name,
        }

    except jwt.ExpiredSignatureError:
        logger.warning("[GET_USER] Token expired")
        raise credentials_exception
    except JWTError as e:
        logger.warning(f"[GET_USER] JWT Error: {type(e).__name__}: {e}")
        raise credentials_exception
    except Exception as e:
        logger.warning(f"[GET_USER] Error: {type(e).__name__}: {e}")
        raise credentials_exception


@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    try:
        user_metadata = {}
        if user.name:
            user_metadata["name"] = user.name

        resp = service_supabase.auth.sign_up(
            {
                "email": user.email,
                "password": user.password,
                "options": {"data": user_metadata},
            }
        )
        if resp.user is None:
            raise HTTPException(status_code=400, detail="Registration failed")

        user_id = resp.user.id
        user_email = resp.user.email or user.email

        access_token = create_access_token({"sub": user_id, "email": user_email})

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(id=user_id, email=user_email, name=user.name),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(response: Response, request: Request):
    try:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
        remember_me = body.get("remember_me", False)

        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password required")

        resp = service_supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        if resp.user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = resp.user.id
        user_email = resp.user.email or email

        user_metadata = resp.user.user_metadata or {}
        name = user_metadata.get("name")

        access_token = create_access_token({"sub": user_id, "email": user_email})
        refresh_token = create_refresh_token({"sub": user_id, "email": user_email})
        logger.info(f"[LOGIN] Created tokens for user: {user_id}")

        refresh_cookie_max_age = 60 * 60 * 24 * 30 if remember_me else None
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="none",
            max_age=refresh_cookie_max_age,
            path="/",
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(id=user_id, email=user_email, name=name),
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh", response_model=Token)
async def refresh_token(response: Response, request: Request):
    refresh_token = request.cookies.get("refresh_token")
    logger.info(f"[REFRESH] Cookie present: {bool(refresh_token)}")
    logger.info(f"[REFRESH] Cookie value: {refresh_token[:30] if refresh_token else 'None'}...")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = verify_refresh_token(refresh_token)
    if not payload:
        logger.warning("[REFRESH] Token verification failed")
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    user_email = payload.get("email")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        user_resp = service_supabase.auth.admin.get_user_by_id(user_id)
        if not user_resp.user:
            raise HTTPException(status_code=404, detail="User not found")
        user_metadata = user_resp.user.user_metadata or {}
        name = user_metadata.get("name")
    except Exception:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = create_access_token({"sub": user_id, "email": user_email})
    new_refresh_token = create_refresh_token({"sub": user_id, "email": user_email})

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="none",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=user_email, name=name),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", path="/", samesite="none")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email", ""),
        name=current_user.get("name"),
    )


@router.post("/supabase-token", response_model=Token)
async def get_token_for_supabase_user(response: Response, request: SupabaseTokenRequest):
    """
    Exchange a Supabase-authenticated user for a backend JWT token.
    This is called by the frontend after Google OAuth completes.
    """
    user_id = request.user_id
    user_email = request.email
    user_name = request.name

    try:
        user_resp = service_supabase.auth.admin.get_user_by_id(user_id)
        if not user_resp.user:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid user")

    access_token = create_access_token({"sub": user_id, "email": user_email})
    refresh_token = create_refresh_token({"sub": user_id, "email": user_email})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="none",
        max_age=60 * 60 * 24 * 30,
        path="/",
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=user_email, name=user_name),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=user_email, name=user_name),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )