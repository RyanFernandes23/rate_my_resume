from typing import Protocol


class PaymentRepository(Protocol):
    async def create_order_record(
        self,
        user_id: str,
        razorpay_order_id: str,
        amount_inr: int,
        credits_to_award: int,
    ) -> None:
        ...

    async def find_order(
        self, razorpay_order_id: str, user_id: str
    ) -> dict | None:
        ...

    async def mark_as_paid(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> None:
        ...


class SupabasePaymentRepository:
    def __init__(self, client) -> None:
        self._client = client

    async def create_order_record(
        self,
        user_id: str,
        razorpay_order_id: str,
        amount_inr: int,
        credits_to_award: int,
    ) -> None:
        self._client.table("payment_orders").insert(
            {
                "user_id": user_id,
                "razorpay_order_id": razorpay_order_id,
                "amount_inr": amount_inr,
                "credits_to_award": credits_to_award,
                "status": "created",
            }
        ).execute()

    async def find_order(
        self, razorpay_order_id: str, user_id: str
    ) -> dict | None:
        response = (
            self._client.table("payment_orders")
            .select("*")
            .eq("razorpay_order_id", razorpay_order_id)
            .eq("user_id", user_id)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None

    async def mark_as_paid(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> None:
        self._client.table("payment_orders").update(
            {
                "status": "paid",
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            }
        ).eq("razorpay_order_id", razorpay_order_id).execute()


class InMemoryPaymentRepository:
    def __init__(self) -> None:
        self._orders: dict[str, dict] = {}

    async def create_order_record(
        self,
        user_id: str,
        razorpay_order_id: str,
        amount_inr: int,
        credits_to_award: int,
    ) -> None:
        self._orders[razorpay_order_id] = {
            "razorpay_order_id": razorpay_order_id,
            "user_id": user_id,
            "amount_inr": amount_inr,
            "credits_to_award": credits_to_award,
            "status": "created",
        }

    async def find_order(
        self, razorpay_order_id: str, user_id: str
    ) -> dict | None:
        order = self._orders.get(razorpay_order_id)
        if order and order["user_id"] == user_id:
            return order
        return None

    async def mark_as_paid(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> None:
        order = self._orders.get(razorpay_order_id)
        if order:
            order["status"] = "paid"
            order["razorpay_payment_id"] = razorpay_payment_id
            order["razorpay_signature"] = razorpay_signature
