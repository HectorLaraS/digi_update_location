from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip()


def _get_required_env(name: str) -> str:
    value = _get_env(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = _get_env(name)
    if value is None:
        return default

    normalized = value.lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False

    raise ValueError(
        f"Invalid boolean value for environment variable {name}: {value}"
    )


def _get_int_env(name: str, default: int) -> int:
    value = _get_env(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid integer value for environment variable {name}: {value}"
        ) from exc


@dataclass(frozen=True)
class Settings:
    # App
    app_host: str
    app_port: int
    app_debug: bool
    app_secret_key: str

    # Digi
    digi_base_url: str
    digi_search_node_by_ip: str
    digi_search_node_by_id: str
    digi_sci_api: str
    digi_user: str
    digi_pass: str
    digi_timeout_seconds: int

    # Reboot / execution
    reboot_enabled_default: bool
    reboot_wait_after_send_seconds: int
    reboot_poll_interval_seconds: int
    reboot_max_check_attempts: int
    reboot_delay_between_routers_seconds: int

    # DB
    db_server: str
    db_database: str
    db_username: str
    db_password: str
    db_driver: str
    db_trust_server_certificate: bool

    # Logging
    log_level: str
    log_dir: str
    log_file_name: str

    @property
    def project_root(self) -> Path:
        return BASE_DIR

    @property
    def log_path(self) -> Path:
        return self.project_root / self.log_dir / self.log_file_name


def load_settings() -> Settings:
    settings = Settings(
        # App
        app_host=_get_required_env("APP_HOST"),
        app_port=_get_int_env("APP_PORT", 5000),
        app_debug=_get_bool_env("APP_DEBUG", False),
        app_secret_key=_get_required_env("APP_SECRET_KEY"),

        # Digi
        digi_base_url=_get_required_env("DIGI_BASE_URL").rstrip("/"),
        digi_search_node_by_ip=_get_required_env("DIGI_SEARCH_NODE_BY_IP"),
        digi_search_node_by_id=_get_required_env("DIGI_SEARCH_NODE_BY_ID"),
        digi_sci_api=_get_required_env("DIGI_SCI_API"),
        digi_user=_get_required_env("DIGI_USER"),
        digi_pass=_get_required_env("DIGI_PASS"),
        digi_timeout_seconds=_get_int_env("DIGI_TIMEOUT_SECONDS", 30),

        # Reboot / execution
        reboot_enabled_default=_get_bool_env("REBOOT_ENABLED_DEFAULT", True),
        reboot_wait_after_send_seconds=_get_int_env(
            "REBOOT_WAIT_AFTER_SEND_SECONDS", 120
        ),
        reboot_poll_interval_seconds=_get_int_env(
            "REBOOT_POLL_INTERVAL_SECONDS", 60
        ),
        reboot_max_check_attempts=_get_int_env(
            "REBOOT_MAX_CHECK_ATTEMPTS", 3
        ),
        reboot_delay_between_routers_seconds=_get_int_env(
            "REBOOT_DELAY_BETWEEN_ROUTERS_SECONDS", 300
        ),

        # DB
        db_server=_get_required_env("DB_SERVER"),
        db_database=_get_required_env("DB_DATABASE"),
        db_username=_get_required_env("DB_USERNAME"),
        db_password=_get_required_env("DB_PASSWORD"),
        db_driver=_get_required_env("DB_DRIVER"),
        db_trust_server_certificate=_get_bool_env(
            "DB_TRUST_SERVER_CERTIFICATE", True
        ),

        # Logging
        log_level=_get_required_env("LOG_LEVEL").upper(),
        log_dir=_get_required_env("LOG_DIR"),
        log_file_name=_get_required_env("LOG_FILE_NAME"),
    )

    return settings


settings = load_settings()