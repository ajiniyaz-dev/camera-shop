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
    session_ttl_seconds: int = Field(default=12 * 60 * 60, ge=60, le=60 * 60 * 24 * 30)
    login_rate_limit_max: int = Field(default=10, ge=1, le=1000)
    login_rate_limit_window_seconds: int = Field(default=15 * 60, ge=1, le=60 * 60 * 24)
    login_rate_limit_max_keys: int = Field(default=10_000, ge=1, le=1_000_000)
    trust_proxy: bool = False
    import_max_bytes: int = Field(default=40 * 1024 * 1024, ge=1024, le=40 * 1024 * 1024)

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

    def cookie_secure(self) -> bool:
        """Production cookies are Secure. Local HTTP development leaves this off."""

        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
