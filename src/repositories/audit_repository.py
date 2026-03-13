from __future__ import annotations

from typing import Any

from src.repositories.db import DatabaseManager


class AuditRepository:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db_manager = db_manager

    def create_execution(
        self,
        executed_by: str,
        csv_name: str | None,
        reboot_enabled: bool,
        execution_status: str = "created",
    ) -> str:
        query = """
        INSERT INTO dbo.audit_log (
            executed_by,
            csv_name,
            reboot_enabled,
            execution_status
        )
        OUTPUT INSERTED.execution_id
        VALUES (?, ?, ?, ?);
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                executed_by,
                csv_name,
                reboot_enabled,
                execution_status,
            )
            row = cursor.fetchone()
            connection.commit()
            return str(row[0])

    def update_execution_validation_summary(
        self,
        execution_id: str,
        total_rows: int,
        ready_count: int,
        not_found_count: int,
        disconnected_count: int,
        execution_status: str = "validated",
    ) -> None:
        query = """
        UPDATE dbo.audit_log
        SET
            total_rows = ?,
            ready_count = ?,
            not_found_count = ?,
            disconnected_count = ?,
            execution_status = ?,
            updated_at = SYSDATETIME()
        WHERE execution_id = ?;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                total_rows,
                ready_count,
                not_found_count,
                disconnected_count,
                execution_status,
                execution_id,
            )
            connection.commit()

    def update_execution_results(
        self,
        execution_id: str,
        updated_count: int,
        rebooted_count: int,
        failed_count: int,
        execution_status: str,
    ) -> None:
        query = """
        UPDATE dbo.audit_log
        SET
            updated_count = ?,
            rebooted_count = ?,
            failed_count = ?,
            execution_status = ?,
            finished_at = SYSDATETIME(),
            updated_at = SYSDATETIME()
        WHERE execution_id = ?;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                updated_count,
                rebooted_count,
                failed_count,
                execution_status,
                execution_id,
            )
            connection.commit()

    def get_execution_by_id(self, execution_id: str) -> dict[str, Any] | None:
        query = """
        SELECT
            audit_id,
            execution_id,
            executed_by,
            started_at,
            finished_at,
            csv_name,
            total_rows,
            ready_count,
            not_found_count,
            disconnected_count,
            updated_count,
            rebooted_count,
            failed_count,
            reboot_enabled,
            execution_status,
            created_at,
            updated_at
        FROM dbo.audit_log
        WHERE execution_id = ?;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, execution_id)
            row = cursor.fetchone()

            if not row:
                return None

            columns = [column[0] for column in cursor.description]
            return dict(zip(columns, row))