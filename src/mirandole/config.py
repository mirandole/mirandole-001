from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required application configuration is missing or invalid."""


def _read_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ConfigError(f"{name} is required")
    return value


@dataclass(frozen=True)
class Settings:
    password: str
    session_secret: str
    database_path: Path
    cookie_secure: bool = True
    france_travail_enabled: bool = False
    france_travail_client_id: str | None = None
    france_travail_client_secret: str | None = None
    adzuna_enabled: bool = False
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None
    adzuna_results_per_page: int = 50
    adzuna_max_results: int = 100

    @classmethod
    def from_env(cls) -> Settings:
        password = _read_required_env("MIRANDOLE_PASSWORD")
        session_secret = _read_required_env("MIRANDOLE_SESSION_SECRET")
        database_path = Path(_read_required_env("MIRANDOLE_DATABASE_PATH"))
        cookie_secure = os.getenv("MIRANDOLE_COOKIE_SECURE", "true").lower()
        france_travail_enabled = os.getenv(
            "MIRANDOLE_FRANCE_TRAVAIL_ENABLED", "false"
        ).lower()
        france_travail_client_id = os.getenv("MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID")
        france_travail_client_secret = os.getenv(
            "MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET"
        )
        adzuna_enabled = os.getenv("MIRANDOLE_ADZUNA_ENABLED", "false").lower()
        adzuna_app_id = os.getenv("MIRANDOLE_ADZUNA_APP_ID")
        adzuna_app_key = os.getenv("MIRANDOLE_ADZUNA_APP_KEY")
        adzuna_results_per_page = _read_optional_int(
            "MIRANDOLE_ADZUNA_RESULTS_PER_PAGE", default=50
        )
        adzuna_max_results = _read_optional_int(
            "MIRANDOLE_ADZUNA_MAX_RESULTS", default=100
        )

        if len(password) < 12:
            raise ConfigError("MIRANDOLE_PASSWORD must be at least 12 characters")
        if len(session_secret) < 32:
            raise ConfigError("MIRANDOLE_SESSION_SECRET must be at least 32 characters")
        if cookie_secure not in {"true", "false"}:
            raise ConfigError("MIRANDOLE_COOKIE_SECURE must be true or false")
        if france_travail_enabled not in {"true", "false"}:
            raise ConfigError("MIRANDOLE_FRANCE_TRAVAIL_ENABLED must be true or false")
        if adzuna_enabled not in {"true", "false"}:
            raise ConfigError("MIRANDOLE_ADZUNA_ENABLED must be true or false")
        if france_travail_enabled == "true" and (
            not france_travail_client_id or not france_travail_client_id.strip()
        ):
            raise ConfigError(
                "MIRANDOLE_FRANCE_TRAVAIL_CLIENT_ID is required when "
                "MIRANDOLE_FRANCE_TRAVAIL_ENABLED is true"
            )
        if france_travail_enabled == "true" and (
            not france_travail_client_secret or not france_travail_client_secret.strip()
        ):
            raise ConfigError(
                "MIRANDOLE_FRANCE_TRAVAIL_CLIENT_SECRET is required when "
                "MIRANDOLE_FRANCE_TRAVAIL_ENABLED is true"
            )
        if adzuna_enabled == "true" and (
            not adzuna_app_id or not adzuna_app_id.strip()
        ):
            raise ConfigError(
                "MIRANDOLE_ADZUNA_APP_ID is required when "
                "MIRANDOLE_ADZUNA_ENABLED is true"
            )
        if adzuna_enabled == "true" and (
            not adzuna_app_key or not adzuna_app_key.strip()
        ):
            raise ConfigError(
                "MIRANDOLE_ADZUNA_APP_KEY is required when "
                "MIRANDOLE_ADZUNA_ENABLED is true"
            )
        if adzuna_results_per_page < 1 or adzuna_results_per_page > 50:
            raise ConfigError(
                "MIRANDOLE_ADZUNA_RESULTS_PER_PAGE must be between 1 and 50"
            )
        if adzuna_max_results < 1:
            raise ConfigError("MIRANDOLE_ADZUNA_MAX_RESULTS must be at least 1")

        return cls(
            password=password,
            session_secret=session_secret,
            database_path=database_path,
            cookie_secure=cookie_secure == "true",
            france_travail_enabled=france_travail_enabled == "true",
            france_travail_client_id=france_travail_client_id,
            france_travail_client_secret=france_travail_client_secret,
            adzuna_enabled=adzuna_enabled == "true",
            adzuna_app_id=adzuna_app_id,
            adzuna_app_key=adzuna_app_key,
            adzuna_results_per_page=adzuna_results_per_page,
            adzuna_max_results=adzuna_max_results,
        )


def _read_optional_int(name: str, *, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
