from pathlib import Path

from pydantic import AliasChoices, Field
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
    # API docs are enabled by default outside production. Override with API_DOCS_ENABLED.
    api_docs_enabled: bool | None = None
    database_url: str = "postgresql+asyncpg://doubow:doubow@localhost:5433/doubow"
    redis_url: str = "redis://localhost:6379"
    # Shared rate-limit key prefix (Redis-backed window limits).
    rate_limit_redis_prefix: str = "ratelimit"
    # If true, Redis limiter backend errors fail closed with 503 instead of bypassing limiter.
    rate_limit_fail_closed: bool = False
    # Background durability switches:
    # - In production, default is Celery for critical workflows unless explicitly overridden.
    # - In non-production, defaults remain in-process for faster local iteration.
    # Set to true/false explicitly to override environment defaults.
    use_celery_for_send: bool | None = None
    use_celery_for_autopilot: bool | None = None
    # Escape hatch: allow FastAPI BackgroundTasks in production for emergency use only.
    allow_inprocess_background_in_production: bool = False

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
    # Optional tier aliases: heavy reasoning (fit debate, prep when set) vs fast drafts/tailor-style tasks.
    # Env: OPENROUTER_MODEL_DEEP or DOUBOW_DEEP_THINK_LLM; OPENROUTER_MODEL_QUICK or DOUBOW_QUICK_THINK_LLM.
    openrouter_model_deep: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_MODEL_DEEP", "DOUBOW_DEEP_THINK_LLM"),
    )
    openrouter_model_quick: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENROUTER_MODEL_QUICK", "DOUBOW_QUICK_THINK_LLM"),
    )
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
    # When True (default), job-fit LLM uses bull/bear sub-prompts before synthesis. False = legacy single JSON call.
    use_llm_fit_debate: bool = True
    # Feature flag: run autopilot executor through LangGraph wrapper (parity mode).
    use_langgraph_autopilot: bool = False
    # Durable SQLite checkpointer path for LangGraph autopilot interrupt/resume state.
    # Used when ``use_langgraph_autopilot_approval_interrupt`` is enabled.
    langgraph_autopilot_checkpoint_db_path: str = "./data/langgraph/autopilot_checkpoints.sqlite"
    # When True with LangGraph autopilot: pause after draft generation via langgraph.types.interrupt until resume.
    # Resume uses POST /me/autopilot/runs/{id}/resume and re-enters LangGraph with a real resume payload.
    use_langgraph_autopilot_approval_interrupt: bool = False
    # Feature flag: log per-node LangGraph autopilot trace events (debug only).
    use_langgraph_autopilot_trace: bool = False
    # Max retries for retryable LangGraph autopilot node failures.
    use_langgraph_autopilot_max_retries: int = 2
    # Persist per-node graph state to autopilot_runs.graph_checkpoint for resume after worker loss.
    use_langgraph_autopilot_checkpoint: bool = True
    # Orchestrator chat: recent transcript bounds (tail of thread for LLM context).
    orchestrator_chat_transcript_max_messages: int = 24
    orchestrator_chat_transcript_max_chars: int = 12000
    # Per-process in-memory throttle windows for expensive agent endpoints.
    # These are best-effort guards; global hard limits should still be enforced at the edge/API gateway.
    agents_chat_window_seconds: int = 60
    agents_chat_max_requests_per_window: int = 30
    agents_pipeline_window_seconds: int = 60
    agents_pipeline_max_requests_per_window: int = 4
    # Autopilot endpoints are expensive (queueing + background orchestration).
    autopilot_run_window_seconds: int = 60
    autopilot_run_max_requests_per_window: int = 4
    autopilot_resume_window_seconds: int = 60
    autopilot_resume_max_requests_per_window: int = 6
    # Admin ingestion endpoints can trigger high-cost upstream sync work.
    ingestion_run_window_seconds: int = 300
    ingestion_run_max_requests_per_window: int = 2
    ingestion_health_window_seconds: int = 60
    ingestion_health_max_requests_per_window: int = 6
    # When True and OpenRouter is configured, classify uncaught NL into structured agent tools (agent-native routing).
    orchestrator_llm_tool_routing: bool = True
    # Blend weight for semantic score in final fit score. 0.0 disables impact.
    semantic_matching_weight: float = 0.25
    # Blend weight for LLM fit signal in final fit score. 0.0 disables impact.
    llm_job_matching_weight: float = 0.2
    # Cost guardrail: only apply LLM fit matching to top-N candidate jobs per user recompute.
    llm_job_matching_top_n: int = 25
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
    # Pagination depth for Greenhouse preset cron-style ingestion (hourly vs daily).
    greenhouse_ingest_hourly_pages: int = 2
    greenhouse_ingest_daily_pages: int = 5
    greenhouse_results_per_page: int = 50
    # Optional defaults when preset endpoint / runner calls without keyword/location overrides.
    greenhouse_ingest_default_keywords: str | None = None
    greenhouse_ingest_default_location: str | None = None
    # System user id used by scheduled catalog ingestion wrappers.
    job_catalog_ingestion_user_id: str = "catalog_ingestion_system"

    # Google Jobs (SerpAPI) — no public unlimited Google API; this uses a third-party SerpAPI plan.
    # See https://serpapi.com/ — subject to account quotas, pricing, and SerpAPI/Google usage terms.
    serpapi_api_key: str | None = None
    google_jobs_default_query: str = "software engineer"
    google_jobs_serp_max_rounds: int = 3
    google_jobs_hl: str = "en"
    google_jobs_gl: str | None = None

    # Scrapling (https://github.com/D4Vinci/Scrapling) — optional job extraction adapter.
    # When SCRAPLING_ENABLED=true: loads SCRAPLING_FIXTURE_JSON_PATH if set, else bundled
    # api_gateway/fixtures/scrapling_sample_jobs.json when scrapling_bundle_fixture is true.
    # Production: prefer scrapling_enabled=false and scrapling_bundle_fixture=false when not using
    # live HTML (explicit seeds + auto Greenhouse job URLs, or JSON-LD from seed pages).
    # scrapling_catalog_in_preset: include Scrapling in POST .../catalog/ingest/preset (after Google Jobs).
    scrapling_enabled: bool = False
    scrapling_fixture_json_path: str | None = None
    scrapling_bundle_fixture: bool = True
    scrapling_catalog_in_preset: bool = True
    scrapling_timeout_s: float = 60.0
    # Comma-separated HTTPS URLs to fetch when no JSON fixture is used (JSON-LD JobPosting in HTML).
    # Example: career pages or individual job pages that embed schema.org JobPosting.
    scrapling_seed_urls: str | None = None
    # When true (default), merge seed URLs derived from GREENHOUSE_BOARD_TOKENS via the public
    # boards-api job list (same service as GreenhouseAdapter) — job detail pages for JSON-LD.
    scrapling_auto_greenhouse_board_seeds: bool = True
    # Max job detail URLs to take per board when building auto seeds (page 1 only).
    scrapling_greenhouse_seed_jobs_per_board: int = 5

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
    # Optional LinkedIn-specific Fernet key. Falls back to GOOGLE_OAUTH_TOKEN_FERNET_KEY for compatibility.
    linkedin_oauth_token_fernet_key: str | None = None

    # Optional shared secret for POST /v1/webhooks/profile-impression (ATS / analytics workers).
    profile_impression_webhook_secret: str | None = None
    # Comma-separated Clerk user ids allowed to call /v1/admin/ingestion/* in production.
    # Example: "user_abc,user_def"
    admin_ingestion_user_ids: str | None = None

    # Portal scanner safety: deny localhost/private targets by default.
    portal_scanner_allow_private_ips: bool = False

    def resolve_openrouter_model(self, use_case: str | None = None) -> str:
        """Resolve model by use-case with fallback to global OpenRouter/Anthropic model."""
        key = (use_case or "").strip().lower()
        deep = self.openrouter_model_deep
        quick = self.openrouter_model_quick
        per_case = {
            "chat": self.openrouter_model_chat,
            "drafts": quick or self.openrouter_model_drafts,
            "prep": deep or self.openrouter_model_prep,
            "resume": self.openrouter_model_resume,
            "deep": deep or self.openrouter_model_prep or self.openrouter_model_resume,
            "quick": quick or self.openrouter_model_drafts,
        }
        candidate = (per_case.get(key) or self.openrouter_model or self.anthropic_model or "").strip()
        return candidate

    def greenhouse_board_tokens_list(self) -> list[str]:
        raw = (self.greenhouse_board_tokens or "").strip()
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()]

    def admin_ingestion_user_ids_list(self) -> list[str]:
        raw = (self.admin_ingestion_user_ids or "").strip()
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
        linked_key = self.linkedin_oauth_token_fernet_key or self.google_oauth_token_fernet_key
        return bool(
            self.linkedin_oauth_client_id
            and self.linkedin_oauth_client_secret
            and self.linkedin_oauth_redirect_uri
            and self.linkedin_oauth_state_secret
            and linked_key
        )

    def use_celery_for_send_effective(self) -> bool:
        if self.use_celery_for_send is not None:
            return self.use_celery_for_send
        return self.environment.lower() == "production"

    def use_celery_for_autopilot_effective(self) -> bool:
        if self.use_celery_for_autopilot is not None:
            return self.use_celery_for_autopilot
        return self.environment.lower() == "production"

    def api_docs_enabled_effective(self) -> bool:
        if self.api_docs_enabled is not None:
            return self.api_docs_enabled
        return self.environment.lower() != "production"


settings = Settings()
