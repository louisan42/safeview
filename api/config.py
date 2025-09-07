from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
import re

class Settings(BaseSettings):
    # Database DSN (URL style) e.g., postgresql://user:pass@host:5432/db?sslmode=require
    PG_DSN: Optional[str] = None

    # Allowed CORS origins for the frontend
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Pydantic v2 config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

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
            fallback = self._fallback_pg_dsn_from_yaml()
            if fallback:
                self.PG_DSN = fallback

settings = Settings()
