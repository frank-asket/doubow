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
    # When True, enqueue send-after-approve via Celery (`tasks.send_tasks`). Worker must run separately.
    use_celery_for_send: bool = False

    # Optional SMTP for real outbound after approval (email channel). When disabled, send path logs only.
    smtp_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_user: str | None = None
    smtp_password: str | None = None
    outbound_from_email: str | None = None
    # When set, all approval sends go here (testing). Otherwise uses the authenticated user's email.
    outbound_send_recipient_override: str | None = None
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]
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
    openrouter_max_retries: int = 3
    openrouter_retry_base_delay_s: float = 0.5
    openrouter_retry_max_delay_s: float = 8.0
    # Feature flag: use LangChain structured prompting for resume analysis.
    use_langchain: bool = False
    # Feature flag: blend semantic resume/job similarity into fit scoring.
    use_semantic_matching: bool = False
    # Blend weight for semantic score in final fit score. 0.0 disables impact.
    semantic_matching_weight: float = 0.25

    # PostHog (optional). When configured, telemetry is mirrored to PostHog and
    # activation KPI is sourced from PostHog events.
    posthog_host: str = "https://eu.posthog.com"
    posthog_project_id: str | None = None
    posthog_personal_api_key: str | None = None
    posthog_project_api_key: str | None = None


settings = Settings()
