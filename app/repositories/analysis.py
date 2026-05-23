from typing import Protocol


class AnalysisRepository(Protocol):
    async def save(
        self, user_id: str, file_name: str, result_json: dict
    ) -> str | None:
        ...

    async def get_by_id(self, analysis_id: str) -> dict | None:
        ...

    async def list_by_user(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> tuple[list[dict], int]:
        ...

    async def delete(self, analysis_id: str, user_id: str) -> bool:
        ...


class SupabaseAnalysisRepository:
    def __init__(self, client) -> None:
        self._client = client

    async def save(
        self, user_id: str, file_name: str, result_json: dict
    ) -> str | None:
        try:
            insert_data = {
                "user_id": user_id,
                "file_name": file_name,
                "result_json": result_json,
            }
            db_response = (
                self._client.table("analyses").insert(insert_data).execute()
            )
            if db_response.data:
                return db_response.data[0]["id"]
        except Exception:
            pass
        return None

    async def get_by_id(self, analysis_id: str) -> dict | None:
        resp = (
            self._client.table("analyses")
            .select("*")
            .eq("id", analysis_id)
            .single()
            .execute()
        )
        return resp.data if resp.data else None

    async def list_by_user(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> tuple[list[dict], int]:
        offset = (page - 1) * limit
        resp = (
            self._client.table("analyses")
            .select("id, created_at, file_name, target_tier", count="exact")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return resp.data or [], resp.count or 0

    async def delete(self, analysis_id: str, user_id: str) -> bool:
        resp = (
            self._client.table("analyses")
            .delete()
            .eq("id", analysis_id)
            .eq("user_id", user_id)
            .execute()
        )
        return bool(resp.data)


class InMemoryAnalysisRepository:
    def __init__(self) -> None:
        self._analyses: dict[str, dict] = {}
        self._counter = 0

    async def save(
        self, user_id: str, file_name: str, result_json: dict
    ) -> str | None:
        self._counter += 1
        analysis_id = str(self._counter)
        self._analyses[analysis_id] = {
            "id": analysis_id,
            "user_id": user_id,
            "file_name": file_name,
            "result_json": result_json,
            "created_at": "2026-01-01T00:00:00Z",
            "target_tier": None,
        }
        return analysis_id

    async def get_by_id(self, analysis_id: str) -> dict | None:
        return self._analyses.get(analysis_id)

    async def list_by_user(
        self, user_id: str, page: int = 1, limit: int = 10
    ) -> tuple[list[dict], int]:
        items = [
            a
            for a in self._analyses.values()
            if a["user_id"] == user_id
        ]
        items.sort(key=lambda a: a["created_at"], reverse=True)
        total = len(items)
        start = (page - 1) * limit
        return items[start : start + limit], total

    async def delete(self, analysis_id: str, user_id: str) -> bool:
        item = self._analyses.get(analysis_id)
        if item and item["user_id"] == user_id:
            del self._analyses[analysis_id]
            return True
        return False
