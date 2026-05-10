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

    @classmethod
    def from_env(cls) -> Settings:
        password = _read_required_env("MIRANDOLE_PASSWORD")
        session_secret = _read_required_env("MIRANDOLE_SESSION_SECRET")
        database_path = Path(_read_required_env("MIRANDOLE_DATABASE_PATH"))
        cookie_secure = os.getenv("MIRANDOLE_COOKIE_SECURE", "true").lower()

        if len(password) < 12:
            raise ConfigError("MIRANDOLE_PASSWORD must be at least 12 characters")
        if len(session_secret) < 32:
            raise ConfigError("MIRANDOLE_SESSION_SECRET must be at least 32 characters")
        if cookie_secure not in {"true", "false"}:
            raise ConfigError("MIRANDOLE_COOKIE_SECURE must be true or false")

        return cls(
            password=password,
            session_secret=session_secret,
            database_path=database_path,
            cookie_secure=cookie_secure == "true",
        )
