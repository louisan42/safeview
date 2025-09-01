from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Database DSN (URL style) e.g., postgresql://user:pass@host:5432/db?sslmode=require
    PG_DSN: Optional[str] = None

    # Allowed CORS origins for the frontend
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
