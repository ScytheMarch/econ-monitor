"""Global settings loaded from environment variables / Streamlit secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (don't override existing env vars —
# Streamlit Cloud sets secrets as env vars and we don't want to clobber them)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_env_file = _PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)


def _get_secret(key: str, default: str = "") -> str:
    """Get a secret from Streamlit Cloud secrets, then fall back to env var.

    Streamlit secrets may not be available at import time, so this is called
    lazily when the value is first accessed.
    """
    # 1. Try Streamlit secrets (works on Streamlit Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            val = st.secrets[key]
            if val:
                return str(val)
    except (KeyError, AttributeError, Exception):
        pass
    # 2. Fall back to environment variable
    return os.getenv(key, default)


class Settings:
    """App settings with lazy secret resolution for Streamlit Cloud compatibility."""

    def __init__(self):
        self._cache: dict[str, str] = {}

    @property
    def fred_api_key(self) -> str:
        return _get_secret("FRED_API_KEY")

    @property
    def gemini_api_key(self) -> str:
        return _get_secret("GEMINI_API_KEY")

    @property
    def changedetection_url(self) -> str:
        return os.getenv("CHANGEDETECTION_URL", "http://localhost:5000")

    @property
    def changedetection_api_key(self) -> str:
        return os.getenv("CHANGEDETECTION_API_KEY", "")

    @property
    def webhook_port(self) -> int:
        return int(os.getenv("WEBHOOK_PORT", "8001"))

    @property
    def streamlit_port(self) -> int:
        return int(os.getenv("STREAMLIT_PORT", "8501"))

    @property
    def poll_interval_minutes(self) -> int:
        return int(os.getenv("POLL_INTERVAL_MINUTES", "15"))

    @property
    def project_root(self) -> Path:
        return _PROJECT_ROOT

    @property
    def db_path(self) -> Path:
        return _PROJECT_ROOT / "data" / "econ_monitor.db"

    @property
    def default_lookback_years(self) -> int:
        return 5

    @property
    def dashboard_refresh_seconds(self) -> int:
        return 60


# Singleton
settings = Settings()
