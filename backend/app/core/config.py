from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Code Review Platform API"
    app_version: str = "0.1.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/code_review_db",
        alias="DATABASE_URL",
    )
    enable_llm_review: bool = Field(default=True, alias="ENABLE_LLM_REVIEW")
    llm_review_provider: str = Field(default="azure_foundry", alias="LLM_REVIEW_PROVIDER")
    azure_foundry_endpoint: str | None = Field(default=None, alias="AZURE_FOUNDRY_ENDPOINT")
    azure_foundry_key: str | None = Field(default=None, alias="AZURE_FOUNDRY_KEY")
    azure_foundry_model: str = Field(default="gpt-5.4", alias="AZURE_FOUNDRY_MODEL")
    azure_foundry_api_version: str | None = Field(
        default=None,
        alias="AZURE_FOUNDRY_API_VERSION",
    )
    azure_foundry_reasoning_effort: str = Field(
        default="medium",
        alias="AZURE_FOUNDRY_REASONING_EFFORT",
    )
    azure_foundry_max_completion_tokens: int = Field(
        default=5000,
        alias="AZURE_FOUNDRY_MAX_COMPLETION_TOKENS",
    )
    jwt_secret: str = Field(default="change-me-in-local-env", alias="JWT_SECRET")
    graphql_debug: bool = Field(default=True, alias="GRAPHQL_DEBUG")
    frontend_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="FRONTEND_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def parse_csv_setting(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]
