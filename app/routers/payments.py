import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from datetime import datetime
import razorpay
import hmac
import hashlib
from app.routers.auth import get_current_user
from app.db import settings, service_supabase

logger = logging.getLogger(__name__)


def _mask_id(user_id: str) -> str:
    return user_id[:8] + "..." if user_id else "unknown"

router = APIRouter(prefix="/payments", tags=["payments"])

razorpay_client = razorpay.Client(
    auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
)

CREDIT_PACKS = [
    {
        "id": "basic",
        "label": "Basic",
        "credits": 1,
        "amount_usd": 199,
        "best_value": False,
    },
    {
        "id": "pro",
        "label": "Pro",
        "credits": 5,
        "amount_usd": 799,
        "best_value": True,
    },
    {
        "id": "premium",
        "label": "Premium",
        "credits": 10,
        "amount_usd": 1299,
        "best_value": False,
    },
]


class CreateOrderRequest(BaseModel):
    pack_id: str


class CreateOrderResponse(BaseModel):
    order_id: str
    amount_usd: int
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    success: bool
    credits_added: int
    new_balance: int


@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    request: CreateOrderRequest, current_user: dict = Depends(get_current_user)
):
    """Create a Razorpay order for credit purchase"""
    pack = next((p for p in CREDIT_PACKS if p["id"] == request.pack_id), None)
    if not pack:
        raise HTTPException(status_code=400, detail="Invalid pack_id")

    user_id = current_user["id"]

    try:
        logger.info(f"Creating order for user: {_mask_id(user_id)}, pack: {request.pack_id}")
        order = razorpay_client.order.create(
            {
                "amount": pack["amount_usd"],
                "currency": "USD",
                "receipt": f"{user_id[:8]}_{int(datetime.now().timestamp())}",
            }
        )
        logger.info(f"Razorpay order created: {order['id']}")

        service_supabase.table("payment_orders").insert(
            {
                "user_id": user_id,
                "razorpay_order_id": order["id"],
                "amount_usd": pack["amount_usd"],
                "credits_to_award": pack["credits"],
                "status": "created",
            }
        ).execute()
        logger.info(f"Order saved to Supabase")

        return CreateOrderResponse(
            order_id=order["id"],
            amount_usd=pack["amount_usd"],
            currency="USD",
            key_id=settings.razorpay_key_id,
        )
    except Exception as e:
        logger.exception(f"Failed to create order: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    request: VerifyPaymentRequest, current_user: dict = Depends(get_current_user)
):
    """Verify Razorpay payment and add credits"""
    user_id = current_user["id"]

    generated_signature = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{request.razorpay_order_id}|{request.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if generated_signature != request.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    order_response = (
        service_supabase.table("payment_orders")
        .select("*")
        .eq("razorpay_order_id", request.razorpay_order_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not order_response.data:
        raise HTTPException(status_code=404, detail="Order not found")

    order = order_response.data[0]
    credits_to_add = order["credits_to_award"]

    service_supabase.table("payment_orders").update(
        {
            "status": "paid",
            "razorpay_payment_id": request.razorpay_payment_id,
            "razorpay_signature": request.razorpay_signature,
        }
    ).eq("razorpay_order_id", request.razorpay_order_id).execute()

    rpc_result = service_supabase.rpc(
        "add_credits",
        {
            "p_user_id": user_id,
            "p_amount": credits_to_add,
            "p_type": "purchase",
            "p_description": "Razorpay payment",
            "p_metadata": {"order_id": request.razorpay_order_id},
        },
    ).execute()

    if rpc_result.data and isinstance(rpc_result.data, dict):
        new_balance = rpc_result.data.get("new_balance", 0)
    else:
        cred_resp = (
            service_supabase.table("user_credits")
            .select("credits")
            .eq("user_id", user_id)
            .execute()
        )
        new_balance = cred_resp.data[0]["credits"] if cred_resp.data else credits_to_add

    return VerifyPaymentResponse(
        success=True, credits_added=credits_to_add, new_balance=new_balance
    )


@router.get("/packs")
async def get_credit_packs():
    return CREDIT_PACKS


@router.post("/webhook")
async def razorpay_webhook(request: Request):
    razorpay_signature = request.headers.get("X-Razorpay-Signature")
    if not razorpay_signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    payload = await request.body()

    generated_signature = hmac.new(
        settings.razorpay_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(generated_signature, razorpay_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = await request.json()
    event_type = event.get("event")

    if event_type == "payment_link.paid":
        logger.info(f"Payment succeeded for order {event['payload']['payment_link']['id']}")
    elif event_type == "payment_link.failed":
        logger.info(f"Payment failed for order {event['payload']['payment_link']['id']}")

    return {"status": "success"}
