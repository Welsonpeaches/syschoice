"""Runtime configuration, driven by environment variables."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    # Version stamped onto every stored result so old records stay interpretable.
    QUIZ_VERSION = "1.0"

    DB_PATH = os.environ.get("SYSCHOICE_DB", str(BASE_DIR / "data" / "app.db"))

    # Admin area is protected by a shared token sent in the X-Admin-Token header.
    ADMIN_TOKEN = os.environ.get("SYSCHOICE_ADMIN_TOKEN", "syschoice-admin")

    SECRET_KEY = os.environ.get("SYSCHOICE_SECRET", "dev-only-secret")

    # Simple per-IP throttle for the assess endpoint.
    RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("SYSCHOICE_RATE_WINDOW", "60"))
    RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("SYSCHOICE_RATE_MAX", "30"))

    CORS_ORIGINS = os.environ.get(
        "SYSCHOICE_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")

    # Optional LLM-written commentary on the result page. Everything works
    # without it; when no key is configured the feature is simply absent.
    LLM_API_KEY = os.environ.get("SYSCHOICE_LLM_API_KEY", "")
    LLM_BASE_URL = os.environ.get("SYSCHOICE_LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.environ.get("SYSCHOICE_LLM_MODEL", "gpt-4o-mini")
    LLM_TIMEOUT = int(os.environ.get("SYSCHOICE_LLM_TIMEOUT", "45"))
