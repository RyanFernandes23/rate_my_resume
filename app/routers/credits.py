from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.routers.auth import get_current_user
from app.db import service_supabase

router = APIRouter(prefix="/credits", tags=["credits"])


class CreditsResponse(BaseModel):
    credits: int


@router.get("", response_model=CreditsResponse)
async def get_credits(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    response = (
        service_supabase.table("user_credits")
        .select("credits")
        .eq("user_id", user_id)
        .execute()
    )

    if response.data:
        return CreditsResponse(credits=response.data[0]["credits"])
    return CreditsResponse(credits=0)
