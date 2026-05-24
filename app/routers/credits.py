from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import service_supabase
from app.routers.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])


class CreditsResponse(BaseModel):
    credits: int


def _mask_id(user_id: str) -> str:
    return user_id[:8] + "..." if user_id else "unknown"


@router.get("", response_model=CreditsResponse)
async def get_credits(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    logger.info(f"Credits lookup for user {_mask_id(user_id)}")

    try:
        response = service_supabase.table("user_credits").select("credits").eq("user_id", user_id).execute()

        if not response.data:
            return CreditsResponse(credits=0)

        credits = response.data[0]["credits"]
        return CreditsResponse(credits=credits)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Credits error for user {_mask_id(user_id)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/deduct")
async def deduct_credit(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    logger.info(f"Deducting credit for user {_mask_id(user_id)}")

    existing = service_supabase.table("user_credits").select("credits").eq("user_id", user_id).execute()

    if not existing.data:
        logger.warning(f"No credits row for {_mask_id(user_id)}")
        raise HTTPException(status_code=400, detail="No credits available")

    current = existing.data[0]["credits"]

    if current < 1:
        raise HTTPException(status_code=400, detail="No credits available")

    new_balance = current - 1
    service_supabase.table("user_credits").update({"credits": new_balance}).eq("user_id", user_id).execute()

    logger.info(f"Credit deducted. New balance: {new_balance}")
    return {"remainingCredits": new_balance}
