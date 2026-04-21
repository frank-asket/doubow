from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_API_DIR = Path(__file__).resolve().parent
# …/backend/api_gateway -> repo root is …/doubow (two levels up)
_REPO_ROOT = _API_DIR.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(_REPO_ROOT / ".env"),
            str(_API_DIR / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Doubow API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://doubow:doubow@localhost:5433/doubow"
    redis_url: str = "redis://localhost:6379"
    cors_origins: list[str] = ["http://localhost:3000"]
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    # Local filesystem root for uploaded resumes (relative paths are resolved from cwd).
    resume_storage_dir: str = "./data/resumes"

    # LLM (optional). When OPENROUTER_API_KEY is set, resume analysis uses OpenRouter.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    openrouter_api_key: str | None = None
    # OpenRouter requires `provider/model` (see openrouter.ai/models). Default: Claude Sonnet 4.6.
    openrouter_model: str = "anthropic/claude-sonnet-4.6"
    openrouter_api_url: str = "https://openrouter.ai/api/v1"
    # OpenRouter optional attribution header (e.g. your app URL).
    openrouter_http_referer: str | None = "http://localhost:3000"


settings = Settings()
