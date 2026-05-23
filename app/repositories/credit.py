from typing import Protocol


class CreditRepository(Protocol):
    async def get_balance(self, user_id: str) -> int:
        ...

    async def deduct(
        self, user_id: str, description: str = "Resume analysis"
    ) -> bool:
        ...

    async def refund(self, user_id: str, reason: str = "Analysis failed") -> bool:
        ...


class SupabaseCreditRepository:
    def __init__(self, client) -> None:
        self._client = client

    async def get_balance(self, user_id: str) -> int:
        response = (
            self._client.table("user_credits")
            .select("credits")
            .eq("user_id", user_id)
            .execute()
        )
        if response.data:
            return response.data[0]["credits"]
        return 0

    async def deduct(
        self, user_id: str, description: str = "Resume analysis"
    ) -> bool:
        try:
            rpc_result = self._client.rpc(
                "use_credit",
                {"p_user_id": user_id, "p_description": description},
            ).execute()
            if (
                rpc_result.data
                and isinstance(rpc_result.data, dict)
                and rpc_result.data.get("success", False)
            ):
                return True
        except Exception:
            pass
        return False

    async def refund(self, user_id: str, reason: str = "Analysis failed") -> bool:
        try:
            from datetime import datetime

            rpc_result = self._client.rpc(
                "add_credits",
                {
                    "p_user_id": user_id,
                    "p_amount": 1,
                    "p_type": "refund",
                    "p_description": reason,
                    "p_metadata": {"refunded_at": datetime.utcnow().isoformat()},
                },
            ).execute()
            if rpc_result.data:
                return True
        except Exception:
            pass
        return False


class InMemoryCreditRepository:
    def __init__(self) -> None:
        self._balances: dict[str, int] = {}

    async def get_balance(self, user_id: str) -> int:
        return self._balances.get(user_id, 0)

    async def deduct(
        self, user_id: str, description: str = "Resume analysis"
    ) -> bool:
        current = self._balances.get(user_id, 0)
        if current < 1:
            return False
        self._balances[user_id] = current - 1
        return True

    async def refund(self, user_id: str, reason: str = "Analysis failed") -> bool:
        self._balances[user_id] = self._balances.get(user_id, 0) + 1
        return True
