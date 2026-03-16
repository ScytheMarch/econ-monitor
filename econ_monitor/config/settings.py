"""Global settings loaded from environment variables / Streamlit secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=True)


def _get_secret(key: str, default: str = "") -> str:
    """Get a secret from Streamlit Cloud secrets, then fall back to env var."""
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


@dataclass(frozen=True)
class Settings:
    # API keys
    fred_api_key: str = field(default_factory=lambda: _get_secret("FRED_API_KEY"))
    gemini_api_key: str = field(default_factory=lambda: _get_secret("GEMINI_API_KEY"))

    # changedetection.io
    changedetection_url: str = field(
        default_factory=lambda: os.getenv("CHANGEDETECTION_URL", "http://localhost:5000")
    )
    changedetection_api_key: str = field(
        default_factory=lambda: os.getenv("CHANGEDETECTION_API_KEY", "")
    )

    # Service ports
    webhook_port: int = field(
        default_factory=lambda: int(os.getenv("WEBHOOK_PORT", "8001"))
    )
    streamlit_port: int = field(
        default_factory=lambda: int(os.getenv("STREAMLIT_PORT", "8501"))
    )

    # Polling
    poll_interval_minutes: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
    )

    # Paths
    project_root: Path = _PROJECT_ROOT
    db_path: Path = field(default_factory=lambda: _PROJECT_ROOT / "data" / "econ_monitor.db")

    # Data defaults
    default_lookback_years: int = 5
    dashboard_refresh_seconds: int = 60


# Singleton
settings = Settings()
