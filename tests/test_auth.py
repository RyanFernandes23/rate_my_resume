import json
import base64

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.routers.auth import LoginRequest
from unittest.mock import patch, MagicMock

from app.main import app

SUPABASE_URL = "https://boprrifmusvilqneyoep.supabase.co"
COOKIE_NAME = "sb-boprrifmusvilqneyoep-auth-token"


def _make_supabase_session_cookie(access_token="test-supabase-token"):
    session = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600,
        "refresh_token": "test-refresh-token",
        "user": {"id": "test-user-id", "email": "test@example.com"},
    }
    raw = json.dumps(session)
    encoded = base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")
    return f"base64-{encoded}"


@pytest.fixture
def mock_supabase_auth():
    mock_user = MagicMock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.user_metadata = {"name": "Test User"}

    mock_response = MagicMock()
    mock_response.user = mock_user

    with patch("app.routers.auth.get_client") as mock_get_client:
        mock_auth_client = MagicMock()
        mock_auth_client.auth.get_user.return_value = mock_response
        mock_get_client.return_value = mock_auth_client
        yield


class TestGetCurrentUser:
    def test_bearer_token_success(self, mock_supabase_auth):
        client = TestClient(app)
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer test-supabase-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_cookie_token_success(self, mock_supabase_auth):
        client = TestClient(app)
        client.cookies.set("access_token", "test-supabase-token")
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_supabase_session_cookie_success(self, mock_supabase_auth):
        client = TestClient(app)
        cookie_value = _make_supabase_session_cookie("test-supabase-token")
        client.cookies.set(COOKIE_NAME, cookie_value)
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id"
        assert data["email"] == "test@example.com"

    def test_no_auth_returns_401(self, mock_supabase_auth):
        client = TestClient(app)
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_bearer_token_without_value_returns_401(self, mock_supabase_auth):
        client = TestClient(app)
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert response.status_code == 401

    def test_wrong_auth_scheme_returns_401(self, mock_supabase_auth):
        client = TestClient(app)
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
        assert response.status_code == 401


class TestLoginRequest:
    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="password123")

    def test_valid_email_accepted(self):
        req = LoginRequest(email="user@example.com", password="password123")
        assert req.email == "user@example.com"

    def test_register_with_short_password_rejected(self):
        with pytest.raises(ValidationError):
            from app.routers.auth import UserCreate
            UserCreate(email="user@example.com", password="short")


class TestLoginResponse:
    @pytest.fixture
    def mock_login(self):
        mock_session = MagicMock()
        mock_session.access_token = "tok_abc"
        mock_session.refresh_token = "tok_ref_abc"
        mock_session.expires_in = 3600

        mock_user = MagicMock()
        mock_user.id = "user-1"
        mock_user.email = "a@b.com"
        mock_user.user_metadata = {"name": "Alice"}

        mock_auth_response = MagicMock()
        mock_auth_response.user = mock_user
        mock_auth_response.session = mock_session

        with patch("app.routers.auth.get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.auth.sign_in_with_password.return_value = mock_auth_response
            mock_get_client.return_value = mock_client
            yield

    def test_login_response_has_no_tokens(self, mock_login):
        client = TestClient(app)
        resp = client.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "testpass1234"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" not in body
        assert "refresh_token" not in body
        assert "token_type" not in body
        assert body["user"]["id"] == "user-1"
