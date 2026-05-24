from fastapi import HTTPException, Depends, Request
from typing import Optional
import logging
from app.db import settings, service_supabase, get_client
from app.routers.auth import get_current_user
from app.lib.cookie_service import CookieService, get_supabase_session_token

logger = logging.getLogger(__name__)


def check_user_credits(user_id: str) -> int:
    """Check user's current credit balance from Supabase."""
    response = (
        service_supabase.table("user_credits")
        .select("credits")
        .eq("user_id", user_id)
        .execute()
    )

    if response.data:
        return response.data[0]["credits"]
    return 0


async def verify_premium_user(current_user: dict = Depends(get_current_user)):
    """
    Dependency to verify if a user is authenticated and has at least 1 credit.
    Returns the user object if successful, otherwise raises 402 Payment Required.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID missing from token")

    credits = check_user_credits(user_id)
    masked = user_id[:8] + "..." if user_id else "unknown"
    logger.info(f"Credit check for user {masked}: {credits} credits")

    if credits < 1:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "insufficient_credits",
                "message": "You don't have enough credits to perform this analysis.",
                "credits": credits,
            },
        )

    return current_user


async def get_optional_user(request: Request) -> Optional[dict]:
    """
    Optional authentication dependency.
    Does not raise exceptions if no token is provided.
    """
    cookie_service = CookieService(secure=settings.cookie_secure)
    token = cookie_service.get_access_token(request)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
    if not token:
        token = get_supabase_session_token(request, settings.supabase_url)
    if not token:
        return None

    try:
        auth_client = get_client(use_service_key=True)
        user_response = auth_client.auth.get_user(token)
        if not user_response.user:
            return None
        user = user_response.user
        user_metadata = user.user_metadata or {}
        return {
            "id": user.id,
            "email": user.email,
            "name": user_metadata.get("name"),
        }
    except Exception:
        return None
