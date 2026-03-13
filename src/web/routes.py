from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request

from src.services.audit_service import AuditService
from src.services.csv_service import CsvService
from src.services.execution_service import ExecutionService
from src.services.validation_service import ValidationService


def register_routes(
    app: Flask,
    audit_service: AuditService,
    csv_service: CsvService,
    validation_service: ValidationService,
    execution_service: ExecutionService,
) -> None:

    @app.get("/health")
    def health() -> tuple:
        return jsonify({"status": "ok"}), 200

    @app.post("/validate")
    def validate_csv() -> tuple:
        if "file" not in request.files:
            return jsonify({"error": "CSV file is required."}), 400

        file = request.files["file"]

        temp_path = Path("input_temp.csv")
        file.save(temp_path)

        rows = csv_service.load_rows(temp_path)
        validation_result = validation_service.validate_rows(rows)

        return (
            jsonify(
                {
                    "valid_rows": [r.__dict__ for r in validation_result.valid_rows],
                    "errors": [str(e) for e in validation_result.errors],
                    "is_valid": validation_result.is_valid,
                }
            ),
            200,
        )

    @app.post("/execute")
    def execute() -> tuple:
        data = request.json or {}

        execution_id = data.get("execution_id")
        routers = data.get("routers")
        reboot_enabled = data.get("reboot_enabled")

        if not execution_id or routers is None:
            return jsonify({"error": "Missing execution_id or routers."}), 400

        # En MVP asumimos que routers ya vienen transformados
        execution_service.execute(
            execution_id=execution_id,
            routers=routers,
            reboot_enabled=reboot_enabled,
        )

        return jsonify({"status": "execution_started"}), 200

    @app.get("/execution/<execution_id>")
    def get_execution(execution_id: str) -> tuple:
        detail = audit_service.get_execution_detail(execution_id)
        return jsonify(detail), 200