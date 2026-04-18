from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "SentinelFlow"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinelflow",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )
    openai_embedding_dimensions: int = Field(
        default=1536, alias="OPENAI_EMBEDDING_DIMENSIONS"
    )
    auto_approval_threshold: float = Field(
        default=0.78, alias="AUTO_APPROVAL_THRESHOLD"
    )
    verifier_pass_threshold: float = Field(
        default=0.8, alias="VERIFIER_PASS_THRESHOLD"
    )
    default_zapier_webhook_url: str | None = Field(
        default=None, alias="DEFAULT_ZAPIER_WEBHOOK_URL"
    )
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="BACKEND_CORS_ORIGINS",
    )

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()

