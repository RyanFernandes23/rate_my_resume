# app/routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
from app.db import settings, service_supabase

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


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
    token_type: str
    user: UserResponse


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(authorization: str = Header(...)) -> dict:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token, settings.supabase_jwt_secret, algorithms=[ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        user_email = payload.get("email", "")

        # Fetch user metadata from Supabase Auth admin API
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

    except JWTError:
        raise credentials_exception


@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    try:
        # Include name in user_metadata
        user_metadata = {}
        if user.name:
            user_metadata["name"] = user.name

        resp = service_supabase.auth.sign_up(
            {
                "email": user.email,
                "password": user.password,
                "options": {"data": user_metadata},  # Store name in metadata
            }
        )
        if resp.user is None:
            raise HTTPException(status_code=400, detail="Registration failed")

        user_id = resp.user.id
        user_email = resp.user.email or user.email

        # Create user_credits record
        try:
            # Check if user already has credits (shouldn't, but safe)
            credits_resp = (
                service_supabase.table("user_credits")
                .select("id")
                .eq("user_id", user_id)
                .execute()
            )
            if not credits_resp.data:
                service_supabase.table("user_credits").insert(
                    {"user_id": user_id, "credits": 3}  # Give 3 free credits
                ).execute()
        except Exception as e:
            print(f"Warning: Could not create credits record - {e}")

        access_token = create_access_token({"sub": user_id, "email": user_email})

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(id=user_id, email=user_email, name=user.name),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        resp = service_supabase.auth.sign_in_with_password(
            {"email": form_data.username, "password": form_data.password}
        )
        if resp.user is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = resp.user.id
        user_email = resp.user.email or form_data.username

        # Get name from user metadata
        user_metadata = resp.user.user_metadata or {}
        name = user_metadata.get("name")

        access_token = create_access_token({"sub": user_id, "email": user_email})

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(id=user_id, email=user_email, name=name),
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user.get("email", ""),
        name=current_user.get("name"),
    )