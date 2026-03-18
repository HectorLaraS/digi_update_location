from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, render_template, request

from src.domain.router_result import RouterResult
from src.services.audit_service import AuditService
from src.services.csv_service import CsvService
from src.services.digi_service import DigiService
from src.services.execution_service import ExecutionService
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


def register_routes(
    app: Flask,
    audit_service: AuditService,
    csv_service: CsvService,
    validation_service: ValidationService,
    digi_service: DigiService,
    execution_service: ExecutionService,
) -> None:
    @app.get("/")
    def index() -> str:
        return render_template("index.html")

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.post("/validate")
    def validate_csv() -> tuple:
        if "file" not in request.files:
            return jsonify({"error": "CSV file is required."}), 400

        file = request.files["file"]
        executed_by = (request.form.get("executed_by") or "").strip() or "unknown"
        reboot_enabled_raw = request.form.get("reboot_enabled", "true").lower()
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
        routers_data = detail["routers"]

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

        execution_service.execute(
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
                    "status": "completed",
                    "execution": _serialize_record(updated_detail["execution"]),
                    "routers": _serialize_records(updated_detail["routers"]),
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