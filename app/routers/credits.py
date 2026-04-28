# app/routers/credits.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import service_supabase
from app.routers.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credits", tags=["credits"])


class CreditsResponse(BaseModel):
    credits: int


@router.get("/credits", response_model=CreditsResponse)
@router.get("", response_model=CreditsResponse)
async def get_credits(current_user: dict = Depends(get_current_user)):
    """Get credits for authenticated user."""
    user_id = current_user["id"]
    logger.info(f"[CREDITS] Step 1: user_id = {user_id}")
    
    try:
        response = service_supabase.table("user_credits").select("credits").eq("user_id", user_id).execute()
        logger.info(f"[CREDITS] Step 2: response.data = {response.data}")
        
        if not response.data:
            logger.warning(f"[CREDITS] Step 3: No credits row found, returning 0")
            return CreditsResponse(credits=0)
        
        credits = response.data[0]["credits"]
        logger.info(f"[CREDITS] Step 4: credits = {credits}")
        
        result = CreditsResponse(credits=credits)
        logger.info(f"[CREDITS] Step 5: returning result = {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CREDITS] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Credits error: {str(e)}")


@router.post("/deduct")
async def deduct_credit(current_user: dict = Depends(get_current_user)):
    """Deduct a credit for authenticated user"""
    user_id = current_user["id"]
    logger.info(f"[CREDITS] Deducting credit for user: {user_id}")
    
    existing = service_supabase.table("user_credits").select("credits").eq("user_id", user_id).execute()
    
    if not existing.data:
        logger.warning(f"[CREDITS] No credits row for {user_id}")
        raise HTTPException(status_code=400, detail="No credits available")
    
    current = existing.data[0]["credits"]
    
    if current < 1:
        raise HTTPException(status_code=400, detail="No credits available")
    
    new_balance = current - 1
    service_supabase.table("user_credits").update({"credits": new_balance}).eq("user_id", user_id).execute()

    logger.info(f"[CREDITS] Credit deducted. New balance: {new_balance}")
    return {"remainingCredits": new_balance}