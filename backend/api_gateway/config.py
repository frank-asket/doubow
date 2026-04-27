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
        # Production web (override / extend via CORS_ORIGINS on Railway).
        "https://doubow.vercel.app",
    ]
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    # Local filesystem root for uploaded resumes (relative paths are resolved from cwd).
    resume_storage_dir: str = "./data/resumes"

    # LLM (optional). When OPENROUTER_API_KEY is set, resume analysis uses OpenRouter.
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    openrouter_api_key: str | None = None
    # OpenRouter requires `provider/model` (see openrouter.ai/models).
    # Tiered defaults: dense Qwen3-class baseline + smaller model for high-volume drafts + reasoning model for prep;
    # assistant chat keeps a premium frontier model. Override any tier with OPENROUTER_MODEL_*.
    openrouter_model: str = "qwen/qwen3-32b"
    openrouter_model_chat: str | None = "anthropic/claude-sonnet-4.6"
    openrouter_model_drafts: str | None = "qwen/qwen3-8b"
    openrouter_model_prep: str | None = "deepseek/deepseek-r1-0528"
    openrouter_model_resume: str | None = None
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
    # Feature flag: optional LLM-based resume/job fit signal blended into score.
    use_llm_job_matching: bool = False
    # Feature flag: run autopilot executor through LangGraph wrapper (parity mode).
    use_langgraph_autopilot: bool = False
    # Feature flag: log per-node LangGraph autopilot trace events (debug only).
    use_langgraph_autopilot_trace: bool = False
    # Max retries for retryable LangGraph autopilot node failures.
    use_langgraph_autopilot_max_retries: int = 2
    # Persist per-node graph state to autopilot_runs.graph_checkpoint for resume after worker loss.
    use_langgraph_autopilot_checkpoint: bool = True
    # Orchestrator chat: recent transcript bounds (tail of thread for LLM context).
    orchestrator_chat_transcript_max_messages: int = 24
    orchestrator_chat_transcript_max_chars: int = 12000
    # Blend weight for semantic score in final fit score. 0.0 disables impact.
    semantic_matching_weight: float = 0.25
    # Blend weight for LLM fit signal in final fit score. 0.0 disables impact.
    llm_job_matching_weight: float = 0.2
    # Fallback lexical overlap blend when semantic matcher is disabled/unavailable.
    lexical_matching_weight: float = 0.45
    # Jobs list cache TTL (seconds). Default: 6 hours.
    jobs_cache_ttl_seconds: int = 21600
    # Provider connectors (optional) for global job catalog ingestion.
    adzuna_api_url: str = "https://api.adzuna.com/v1/api/jobs"
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    adzuna_country: str = "gb"
    adzuna_results_per_page: int = 50
    # Pagination depth for preset cron-style ingestion (hourly vs daily).
    adzuna_ingest_hourly_pages: int = 2
    adzuna_ingest_daily_pages: int = 5
    # Optional defaults when cron calls preset endpoint without query overrides.
    adzuna_ingest_default_keywords: str | None = None
    adzuna_ingest_default_location: str | None = None
    greenhouse_api_url: str = "https://boards-api.greenhouse.io/v1/boards"
    # Comma-separated board tokens, e.g. "openai,notion,figma".
    greenhouse_board_tokens: str | None = None
    # System user id used by scheduled catalog ingestion wrappers.
    job_catalog_ingestion_user_id: str = "catalog_ingestion_system"

    # PostHog (optional). When configured, telemetry is mirrored to PostHog and
    # activation KPI is sourced from PostHog events.
    posthog_host: str = "https://eu.posthog.com"
    posthog_project_id: str | None = None
    posthog_personal_api_key: str | None = None
    posthog_project_api_key: str | None = None

    # Observability
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.0

    # Google OAuth (Gmail API send). Create OAuth client (Web) in Google Cloud Console.
    google_oauth_client_id: str | None = None
    google_oauth_client_secret: str | None = None
    # Backend callback URL registered in Google Cloud (e.g. http://localhost:8000/v1/integrations/google/callback).
    google_oauth_redirect_uri: str | None = None
    # Browser redirect after connect success/failure (query params: google_connected=1 or google_error=...).
    google_oauth_frontend_redirect_uri: str = "http://localhost:3000/settings"
    # HMAC secret for OAuth `state` (use a long random string).
    google_oauth_state_secret: str | None = None
    # Fernet key for encrypting refresh tokens at rest (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
    google_oauth_token_fernet_key: str | None = None
    # After approve (email channel): ``draft`` = Gmail API draft in user's mailbox first; ``send`` = immediate send.
    # Draft requires OAuth with gmail.compose scope (users reconnect after upgrade).
    gmail_approval_handoff: str = "draft"

    # LinkedIn OAuth (outbound note handoff).
    linkedin_oauth_client_id: str | None = None
    linkedin_oauth_client_secret: str | None = None
    linkedin_oauth_redirect_uri: str | None = None
    linkedin_oauth_frontend_redirect_uri: str = "http://localhost:3000/settings"
    linkedin_oauth_state_secret: str | None = None

    # Optional shared secret for POST /v1/webhooks/profile-impression (ATS / analytics workers).
    profile_impression_webhook_secret: str | None = None

    # Portal scanner safety: deny localhost/private targets by default.
    portal_scanner_allow_private_ips: bool = False

    def resolve_openrouter_model(self, use_case: str | None = None) -> str:
        """Resolve model by use-case with fallback to global OpenRouter/Anthropic model."""
        key = (use_case or "").strip().lower()
        per_case = {
            "chat": self.openrouter_model_chat,
            "drafts": self.openrouter_model_drafts,
            "prep": self.openrouter_model_prep,
            "resume": self.openrouter_model_resume,
        }
        candidate = (per_case.get(key) or self.openrouter_model or self.anthropic_model or "").strip()
        return candidate

    def greenhouse_board_tokens_list(self) -> list[str]:
        raw = (self.greenhouse_board_tokens or "").strip()
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]

    def google_oauth_is_configured(self) -> bool:
        return bool(
            self.google_oauth_client_id
            and self.google_oauth_client_secret
            and self.google_oauth_redirect_uri
            and self.google_oauth_state_secret
            and self.google_oauth_token_fernet_key
        )

    def linkedin_oauth_is_configured(self) -> bool:
        return bool(
            self.linkedin_oauth_client_id
            and self.linkedin_oauth_client_secret
            and self.linkedin_oauth_redirect_uri
            and self.linkedin_oauth_state_secret
            and self.google_oauth_token_fernet_key
        )


settings = Settings()
