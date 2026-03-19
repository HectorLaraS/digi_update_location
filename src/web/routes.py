from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request

from src.domain.router_result import RouterResult
from src.services.audit_service import AuditService
from src.services.csv_service import CsvService
from src.services.digi_service import DigiService
from src.services.execution_manager import ExecutionManager
from src.services.execution_service import ExecutionService
from src.services.manual_reboot_manager import ManualRebootManager
from src.services.refresh_service import RefreshService
from src.services.single_router_reboot_service import SingleRouterRebootService
from src.services.validation_service import ValidationService


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _serialize_records(records: list[dict]) -> list[dict]:
    serialized: list[dict] = []
    for record in records:
        serialized.append({key: _serialize_value(val) for key, val in record.items()})
    return serialized


def _serialize_record(record: dict | None) -> dict | None:
    if record is None:
        return None
    return {key: _serialize_value(val) for key, val in record.items()}


def _build_router_results(routers_data: list[dict]) -> list[RouterResult]:
    router_results: list[RouterResult] = []

    for router in routers_data:
        router_results.append(
            RouterResult(
                execution_id=router["execution_id"],
                ip=router["ip_address"],
                new_location=router["new_location"],
                device_id=router.get("device_id"),
                device_name=router.get("device_name"),
                old_location=router.get("old_location"),
                device_type=router.get("device_type"),
                connection_status=router.get("connection_status_before"),
                system_status=router.get("system_status_before"),
                message=router.get("notes"),
            )
        )

    return router_results


def register_routes(
    app: Flask,
    audit_service: AuditService,
    csv_service: CsvService,
    validation_service: ValidationService,
    digi_service: DigiService,
    execution_service: ExecutionService,
    execution_manager: ExecutionManager,
    refresh_service: RefreshService,
    single_router_reboot_service: SingleRouterRebootService,
    manual_reboot_manager: ManualRebootManager,
) -> None:
    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.get("/execution/<execution_id>/job-status")
    def get_job_status(execution_id: str) -> tuple:
        job = execution_manager.get_job_state(execution_id)
        if job is None:
            return jsonify({"status": "not_found"}), 404

        return (
            jsonify(
                {
                    "execution_id": job.execution_id,
                    "status": job.status,
                    "message": job.message,
                    "paused_router_ip": job.paused_router_ip,
                    "is_running": job.is_running,
                    "is_cancel_requested": job.is_cancel_requested,
                    "current_phase": job.current_phase,
                    "current_router_ip": job.current_router_ip,
                    "current_router_name": job.current_router_name,
                    "processed_count": job.processed_count,
                    "total_count": job.total_count,
                    "countdown_seconds": job.countdown_seconds,
                    "countdown_label": job.countdown_label,
                }
            ),
            200,
        )

    @app.get("/execution/<execution_id>/router/<ip_address>/reboot-status")
    def get_manual_reboot_status(execution_id: str, ip_address: str) -> tuple:
        job = manual_reboot_manager.get_job_state(
            execution_id=execution_id,
            router_ip=ip_address,
        )
        if job is None:
            return jsonify({"status": "not_found"}), 404

        return (
            jsonify(
                {
                    "execution_id": job.execution_id,
                    "router_ip": job.router_ip,
                    "status": job.status,
                    "message": job.message,
                    "is_running": job.is_running,
                    "current_phase": job.current_phase,
                    "attempt": job.attempt,
                    "max_attempts": job.max_attempts,
                    "countdown_seconds": job.countdown_seconds,
                    "countdown_label": job.countdown_label,
                }
            ),
            200,
        )

    @app.post("/validate")
    def validate_csv() -> tuple:
        if "file" not in request.files:
            return jsonify({"error": "CSV file is required."}), 400

        file = request.files["file"]
        executed_by = (request.form.get("executed_by") or "").strip() or "unknown"
        reboot_enabled_raw = request.form.get("reboot_enabled", "false").lower()
        reboot_enabled = reboot_enabled_raw == "true"

        digi_user = (request.form.get("digi_user") or "").strip() or None
        digi_pass = (request.form.get("digi_pass") or "").strip() or None

        input_dir = Path("input")
        input_dir.mkdir(parents=True, exist_ok=True)

        temp_file_name = f"{uuid4()}_{file.filename}"
        temp_path = input_dir / temp_file_name
        file.save(temp_path)

        rows = csv_service.load_rows(temp_path)
        validation_result = validation_service.validate_rows(rows)

        execution_id = audit_service.create_execution(
            executed_by=executed_by,
            csv_name=file.filename,
            reboot_enabled=reboot_enabled,
        )

        router_results: list[RouterResult] = []

        for row in validation_result.valid_rows:
            device = digi_service.search_device_by_ip(
                row.ip,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            if device is None:
                router_results.append(
                    RouterResult(
                        execution_id=execution_id,
                        ip=row.ip,
                        new_location=row.new_location,
                        system_status="not_found",
                        message="Router was not found in Digi.",
                    )
                )
                continue

            if device.connection_status != "connected":
                router_results.append(
                    RouterResult(
                        execution_id=execution_id,
                        ip=row.ip,
                        new_location=row.new_location,
                        device_id=device.id,
                        device_name=device.name,
                        old_location=device.location,
                        device_type=device.d_type,
                        connection_status=device.connection_status,
                        system_status="disconnected",
                        message="Router is disconnected.",
                    )
                )
                continue

            router_results.append(
                RouterResult(
                    execution_id=execution_id,
                    ip=row.ip,
                    new_location=row.new_location,
                    device_id=device.id,
                    device_name=device.name,
                    old_location=device.location,
                    device_type=device.d_type,
                    connection_status=device.connection_status,
                    system_status="ready",
                    message="Router is ready for update.",
                )
            )

        audit_service.save_validation_results(
            execution_id=execution_id,
            router_results=router_results,
        )

        detail = audit_service.get_execution_detail(execution_id)

        return (
            jsonify(
                {
                    "execution_id": execution_id,
                    "validation_errors": [str(e) for e in validation_result.errors],
                    "execution": _serialize_record(detail["execution"]),
                    "routers": _serialize_records(detail["routers"]),
                }
            ),
            200,
        )

    @app.post("/execute")
    def execute() -> tuple:
        data = request.get_json(silent=True) or {}

        execution_id = data.get("execution_id")
        reboot_enabled = data.get("reboot_enabled")
        digi_user = (data.get("digi_user") or "").strip() or None
        digi_pass = (data.get("digi_pass") or "").strip() or None

        if not execution_id:
            return jsonify({"error": "execution_id is required."}), 400

        detail = audit_service.get_execution_detail(execution_id)
        if not detail["execution"]:
            return jsonify({"error": "Execution not found."}), 404

        routers_data = detail["routers"]
        router_results = _build_router_results(routers_data)

        job = execution_manager.start_execution(
            execution_id=execution_id,
            routers=router_results,
            reboot_enabled=reboot_enabled,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        updated_detail = audit_service.get_execution_detail(execution_id)

        return (
            jsonify(
                {
                    "status": job.status,
                    "message": job.message,
                    "paused_router_ip": job.paused_router_ip,
                    "is_running": job.is_running,
                    "execution": _serialize_record(updated_detail["execution"]),
                    "routers": _serialize_records(updated_detail["routers"]),
                }
            ),
            202,
        )

    @app.post("/execution/<execution_id>/continue")
    def continue_execution(execution_id: str) -> tuple:
        data = request.get_json(silent=True) or {}

        reboot_enabled = data.get("reboot_enabled")
        digi_user = (data.get("digi_user") or "").strip() or None
        digi_pass = (data.get("digi_pass") or "").strip() or None

        detail = audit_service.get_execution_detail(execution_id)
        if not detail["execution"]:
            return jsonify({"error": "Execution not found."}), 404

        routers_data = detail["routers"]

        routers_to_continue = [
            router for router in routers_data
            if router.get("system_status_before") == "ready"
            and router.get("system_status_after") is None
        ]

        router_results = _build_router_results(routers_to_continue)

        job = execution_manager.continue_execution(
            execution_id=execution_id,
            routers=router_results,
            reboot_enabled=reboot_enabled,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        updated_detail = audit_service.get_execution_detail(execution_id)

        return (
            jsonify(
                {
                    "status": job.status,
                    "message": job.message,
                    "paused_router_ip": job.paused_router_ip,
                    "is_running": job.is_running,
                    "execution": _serialize_record(updated_detail["execution"]),
                    "routers": _serialize_records(updated_detail["routers"]),
                }
            ),
            202,
        )

    @app.post("/execution/<execution_id>/stop")
    def stop_execution(execution_id: str) -> tuple:
        detail = audit_service.get_execution_detail(execution_id)
        if not detail["execution"]:
            return jsonify({"error": "Execution not found."}), 404

        execution_manager.request_cancel(execution_id)
        audit_service.mark_execution_cancelled(execution_id)

        updated_detail = audit_service.get_execution_detail(execution_id)

        return (
            jsonify(
                {
                    "status": "cancelled",
                    "message": "Execution cancellation requested by the user.",
                    "execution": _serialize_record(updated_detail["execution"]),
                    "routers": _serialize_records(updated_detail["routers"]),
                }
            ),
            200,
        )

    @app.post("/execution/<execution_id>/router/<ip_address>/reboot")
    def reboot_single_router(execution_id: str, ip_address: str) -> tuple:
        data = request.get_json(silent=True) or {}

        digi_user = (data.get("digi_user") or "").strip() or None
        digi_pass = (data.get("digi_pass") or "").strip() or None

        detail = audit_service.get_execution_detail(execution_id)
        if not detail["execution"]:
            return jsonify({"error": "Execution not found."}), 404

        routers_data = detail["routers"]
        target_router = next(
            (router for router in routers_data if router.get("ip_address") == ip_address),
            None,
        )

        if target_router is None:
            return jsonify({"error": "Router not found in execution."}), 404

        job = manual_reboot_manager.start_manual_reboot(
            execution_id=execution_id,
            router_data=target_router,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        updated_detail = audit_service.get_execution_detail(execution_id)

        return (
            jsonify(
                {
                    "status": job.status,
                    "message": job.message,
                    "router_ip": job.router_ip,
                    "is_running": job.is_running,
                    "execution": _serialize_record(updated_detail["execution"]),
                    "routers": _serialize_records(updated_detail["routers"]),
                }
            ),
            202,
        )

    @app.post("/execution/<execution_id>/refresh")
    def refresh_execution(execution_id: str) -> tuple:
        data = request.get_json(silent=True) or {}

        digi_user = (data.get("digi_user") or "").strip() or None
        digi_pass = (data.get("digi_pass") or "").strip() or None

        refreshed_detail = refresh_service.refresh_execution(
            execution_id=execution_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        return (
            jsonify(
                {
                    "status": "refreshed",
                    "execution": _serialize_record(refreshed_detail["execution"]),
                    "routers": _serialize_records(refreshed_detail["routers"]),
                }
            ),
            200,
        )

    @app.get("/execution/<execution_id>")
    def get_execution(execution_id: str) -> tuple:
        detail = audit_service.get_execution_detail(execution_id)

        return (
            jsonify(
                {
                    "execution": _serialize_record(detail["execution"]),
                    "routers": _serialize_records(detail["routers"]),
                }
            ),
            200,
        )