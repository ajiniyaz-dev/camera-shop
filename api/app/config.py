from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PLACEHOLDER_SECRETS = frozenset(
    {
        "",
        "change-me",
        "change-me-to-a-long-random-string",
    }
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_API_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", _API_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(min_length=1)
    session_secret: str = "change-me"
    media_root: str = "/var/lib/catalog/media"
    media_public_base_url: str = "http://localhost/media"
    public_site_url: str = "http://localhost"
    api_internal_url: str = "http://127.0.0.1:8000"
    debug: bool = False
    app_env: str = "local"

    @field_validator("database_url")
    @classmethod
    def database_url_is_postgresql(cls, value: str) -> str:
        if not value.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return value

    @model_validator(mode="after")
    def production_guards(self) -> "Settings":
        if self.app_env != "production":
            return self
        if self.session_secret in _PLACEHOLDER_SECRETS:
            raise ValueError(
                "SESSION_SECRET must be a non-placeholder value when APP_ENV is production"
            )
        if self.debug:
            raise ValueError("DEBUG must be false when APP_ENV is production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
