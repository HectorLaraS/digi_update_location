from __future__ import annotations

from flask import Flask

from src.config.settings import settings
from pathlib import Path
from src.config.logging_config import setup_logging

from src.repositories.db import build_database_manager
from src.repositories.audit_repository import AuditRepository
from src.repositories.router_repository import RouterRepository

from src.services.audit_service import AuditService
from src.services.csv_service import CsvService
from src.services.validation_service import ValidationService
from src.services.digi_service import DigiService
from src.services.execution_service import ExecutionService

from src.web.routes import register_routes


def create_app() -> Flask:
    # --- Logging ---
    logger = setup_logging(
        log_dir=Path(settings.log_dir),
        log_file_name=settings.log_file_name,
        log_level=settings.log_level,
    )

    # --- Flask ---
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.app_secret_key

    # --- Database ---
    db_manager = build_database_manager(settings)

    audit_repository = AuditRepository(db_manager)
    router_repository = RouterRepository(db_manager)

    # --- Services ---
    audit_service = AuditService(
        audit_repository=audit_repository,
        router_repository=router_repository,
    )

    csv_service = CsvService()
    validation_service = ValidationService()

    digi_service = DigiService(settings)

    execution_service = ExecutionService(
        digi_service=digi_service,
        audit_service=audit_service,
        reboot_enabled_default=settings.reboot_enabled_default,
        reboot_wait_after_send_seconds=settings.reboot_wait_after_send_seconds,
        reboot_poll_interval_seconds=settings.reboot_poll_interval_seconds,
        reboot_max_check_attempts=settings.reboot_max_check_attempts,
        reboot_delay_between_routers_seconds=settings.reboot_delay_between_routers_seconds,
    )

    # --- Register routes ---
    register_routes(
        app=app,
        audit_service=audit_service,
        csv_service=csv_service,
        validation_service=validation_service,
        execution_service=execution_service,
    )

    return app


# --- Entry point (for development or service launcher) ---
app = create_app()


if __name__ == "__main__":
    app.run(
        host=settings.app_host,
        port=settings.app_port,
        debug=settings.app_debug,
    )