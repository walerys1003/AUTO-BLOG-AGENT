"""
MasterContentAI - Centralised configuration.

All secrets MUST be supplied via environment variables (see .env.example).
Never hardcode credentials in this file.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


def _env(name: str, default=None, *, required: bool = False, cast=str):
    """Read an env variable with optional cast and required flag."""
    value = os.environ.get(name, default)
    if required and value in (None, ""):
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"See .env.example for the list of expected variables."
        )
    if value is None or value == "":
        return default
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def _csv(name: str, default: str):
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


class Config:
    """Application configuration sourced exclusively from env."""

    # ---- Flask ----
    SESSION_SECRET = _env("SESSION_SECRET", "mastercontentai-change-me")
    DATABASE_URL = _env("DATABASE_URL", "sqlite:///zyga.db")

    # ---- AI / OpenRouter ----
    OPENROUTER_API_KEY = _env("OPENROUTER_API_KEY")
    ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = _env("OPENAI_API_KEY")

    DEFAULT_TOPIC_MODEL = _env("DEFAULT_TOPIC_MODEL", "anthropic/claude-haiku-4.5")
    DEFAULT_CONTENT_MODEL = _env("DEFAULT_CONTENT_MODEL", "anthropic/claude-haiku-4.5")
    DEFAULT_SOCIAL_MODEL = _env("DEFAULT_SOCIAL_MODEL", "anthropic/claude-haiku-4.5")

    # ---- Images ----
    UNSPLASH_API_KEY = _env("UNSPLASH_API_KEY")
    BING_SEARCH_API_KEY = _env("BING_SEARCH_API_KEY")
    GOOGLE_API_KEY = _env("GOOGLE_API_KEY")
    GOOGLE_CSE_ID = _env("GOOGLE_CSE_ID")

    # ---- SEO ----
    SERPAPI_KEY = _env("SERPAPI_KEY")

    # ---- Social Media ----
    FACEBOOK_APP_ID = _env("FACEBOOK_APP_ID")
    FACEBOOK_APP_SECRET = _env("FACEBOOK_APP_SECRET")
    TWITTER_API_KEY = _env("TWITTER_API_KEY")
    TWITTER_API_SECRET = _env("TWITTER_API_SECRET")
    LINKEDIN_CLIENT_ID = _env("LINKEDIN_CLIENT_ID")
    LINKEDIN_CLIENT_SECRET = _env("LINKEDIN_CLIENT_SECRET")

    # ---- Application limits ----
    ARTICLES_PER_DAY_PER_BLOG = _env("ARTICLES_PER_DAY_PER_BLOG", 3, cast=int)
    ARTICLE_MIN_LENGTH = _env("ARTICLE_MIN_LENGTH", 1200, cast=int)
    ARTICLE_MAX_LENGTH = _env("ARTICLE_MAX_LENGTH", 1600, cast=int)
    PUBLISHING_TIMES = _csv("PUBLISHING_TIMES", "08:00,12:00,16:00,20:00")
    LOG_RETENTION_DAYS = _env("LOG_RETENTION_DAYS", 30, cast=int)

    # ---- Production safety ----
    USE_MOCK_ADAPTER = _env("USE_MOCK_ADAPTER", "false").lower() == "true"

    # ---- Scheduler ----
    SCHEDULER_API_ENABLED = True
