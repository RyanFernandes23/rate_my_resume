from supabase import create_client, Client
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    groq_api_key: str
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    supabase_jwt_secret: str
    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str
    secret_key: str
    frontend_url: str = "http://localhost:3000"
    cookie_secure: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Global clients - DO NOT use auth methods (login, sign_up, refresh) on these
# as it will pollute the global state and cause JWT expiry issues.
# Use get_client() for any auth-related operations.
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
service_supabase: Client = create_client(
    settings.supabase_url, settings.supabase_service_key
)


def get_client(use_service_key: bool = False) -> Client:
    """Returns a fresh Supabase client instance."""
    key = settings.supabase_service_key if use_service_key else settings.supabase_anon_key
    return create_client(settings.supabase_url, key)
