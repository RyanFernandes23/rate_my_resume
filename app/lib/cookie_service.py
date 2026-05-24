import json
import base64
from urllib.parse import urlparse

from fastapi import Response, Request
from typing import Optional


ACCESS_TOKEN_MAX_AGE = 3600  # 1 hour, matches JWT expiry
REFRESH_TOKEN_MAX_AGE = 30 * 24 * 3600  # 30 days

BASE64_PREFIX = "base64-"


def get_supabase_session_token(request: Request, supabase_url: str) -> Optional[str]:
    """
    Read the Supabase SSR session cookie (sb-<ref>-auth-token) and extract
    the access_token from it. This lets the backend authenticate users who
    signed in via Supabase (e.g. Google OAuth) without needing the custom
    access_token cookie.
    """
    try:
        hostname = urlparse(supabase_url).hostname
        if not hostname:
            return None
        project_ref = hostname.split(".")[0]
        cookie_name = f"sb-{project_ref}-auth-token"

        raw = request.cookies.get(cookie_name)
        if not raw:
            return None

        if not raw.startswith(BASE64_PREFIX):
            return None

        encoded = raw[len(BASE64_PREFIX):]
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding

        decoded = base64.urlsafe_b64decode(encoded).decode("utf-8")
        session = json.loads(decoded)
        return session.get("access_token")
    except Exception:
        return None


class CookieService:
    def __init__(self, secure: bool = False) -> None:
        self._secure = secure

    def set_auth_cookies(
        self, response: Response, access_token: str, refresh_token: str, expires_in: int
    ) -> None:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=self._secure,
            samesite="lax",
            path="/",
            max_age=expires_in,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=self._secure,
            samesite="lax",
            path="/auth/refresh",
            max_age=REFRESH_TOKEN_MAX_AGE,
        )

    def clear_auth_cookies(self, response: Response) -> None:
        response.delete_cookie("access_token", path="/")
        response.delete_cookie("refresh_token", path="/auth/refresh")

    def get_access_token(self, request: Request) -> Optional[str]:
        return request.cookies.get("access_token")

    def get_refresh_token(self, request: Request) -> Optional[str]:
        return request.cookies.get("refresh_token")
