from fastapi import APIRouter, HTTPException, Depends
from app.routers.auth import get_current_user
from app.db import service_supabase

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
async def list_analyses(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    resp = service_supabase.table("analyses") \
        .select("id, created_at, file_name, target_tier") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    return resp.data or []


@router.get("/{analysis_id}")
async def get_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    resp = service_supabase.table("analyses") \
        .select("*") \
        .eq("id", analysis_id) \
        .single() \
        .execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return resp.data


@router.delete("/{analysis_id}")
async def delete_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    resp = service_supabase.table("analyses") \
        .delete() \
        .eq("id", analysis_id) \
        .eq("user_id", current_user["id"]) \
        .execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"success": True}