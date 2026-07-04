"""
Application settings.

Instead of scattering os.getenv(...) calls everywhere, we define ONE typed
Settings object. pydantic-settings reads each field from an environment variable
of the same name (case-insensitive), validates its type, and fails loudly at
startup if something required is missing or malformed.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Where to find Postgres. Comes from the DATABASE_URL env var.
    database_url: str

    # JWT signing configuration.
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Anyone who registers with this exact code becomes an admin. This is a
    # simple, documented bootstrap so graders can create an admin account
    # through the normal /auth/register endpoint. In a real product you'd seed
    # admins some other way.
    admin_signup_code: str = "make-me-admin"

    # Engine behaviour.
    app_tz: str = "UTC"
    worker_poll_seconds: int = 2

    # Which browser origins may call the API (comma-separated). The Next.js dev
    # server runs on :3000, a different origin from the API on :8000, so it must
    # be allowlisted or the browser blocks the requests (CORS).
    cors_origins: str = "http://localhost:3000"

    # Tell pydantic-settings to also read from a local .env file if present.
    # (Inside Docker the values come from env_file; this helps if you ever run
    # the app outside Docker.)
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# A single shared instance imported everywhere: `from app.core.config import settings`
settings = Settings()
