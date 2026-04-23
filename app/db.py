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
    frontend_url: str = "http://127.0.0.1:3000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
supabase: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
service_supabase: Client = create_client(
    settings.supabase_url, settings.supabase_service_key
)
