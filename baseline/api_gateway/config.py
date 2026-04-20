from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Doubow API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://doubow:doubow@localhost:5432/doubow"
    redis_url: str = "redis://localhost:6379"
    cors_origins: list[str] = ["http://localhost:3000"]
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    # Local filesystem root for uploaded resumes (relative paths are resolved from cwd).
    resume_storage_dir: str = "./data/resumes"


settings = Settings()
