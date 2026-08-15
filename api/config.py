from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import json
import os
import re


def _parse_cors(value: str) -> List[str]:
    raw = value.strip()
    if not raw:
        return []
    if raw.startswith("["):
        parsed = json.loads(raw)
        return [str(x).strip() for x in parsed if str(x).strip()]
    return [x.strip() for x in raw.split(",") if x.strip()]


class Settings(BaseSettings):
    # Database DSN (URL style) e.g., postgresql://user:pass@host:5432/db?sslmode=require
    PG_DSN: Optional[str] = None
    # Railway / Supabase commonly inject DATABASE_URL instead of PG_DSN
    DATABASE_URL: Optional[str] = None

    # Comma-separated or JSON list. Railway env vars are easiest as comma-separated.
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return _parse_cors(self.CORS_ORIGINS)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def coerce_cors_origins(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return ",".join(str(x) for x in v)
        return v

    def _fallback_pg_dsn_from_yaml(self) -> Optional[str]:
        """Attempt to read pg_dsn from etl/config.yaml (local dev convenience).

        We avoid adding a YAML dependency by scanning for a top-level line like:
        pg_dsn: postgresql://...
        """
        try:
            cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "etl", "config.yaml")
            if not os.path.exists(cfg_path):
                return None
            with open(cfg_path, "r", encoding="utf-8") as f:
                for line in f:
                    # ignore commented lines and leading spaces
                    if line.lstrip().startswith("#"):
                        continue
                    m = re.match(r"^\s*pg_dsn\s*:\s*(.+)\s*$", line)
                    if m:
                        return m.group(1).strip()
        except Exception:
            return None
        return None

    def __init__(self, **values):
        super().__init__(**values)
        if not self.PG_DSN:
            if self.DATABASE_URL:
                self.PG_DSN = self.DATABASE_URL
            else:
                fallback = self._fallback_pg_dsn_from_yaml()
                if fallback:
                    self.PG_DSN = fallback


settings = Settings()
