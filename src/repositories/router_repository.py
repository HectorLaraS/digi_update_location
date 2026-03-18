from __future__ import annotations

from typing import Any

from src.domain.router_result import RouterResult
from src.repositories.db import DatabaseManager


class RouterRepository:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db_manager = db_manager

    def insert_router_result(self, router_result: RouterResult) -> None:
        query = """
        INSERT INTO dbo.affected_routers (
            execution_id,
            device_id,
            device_name,
            ip_address,
            old_location,
            new_location,
            device_type,
            connection_status_before,
            system_status_before,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                router_result.execution_id,
                router_result.device_id,
                router_result.device_name,
                router_result.ip,
                router_result.old_location,
                router_result.new_location,
                router_result.device_type,
                router_result.connection_status,
                router_result.system_status,
                router_result.message,
            )
            connection.commit()

    def update_router_after_execution(
        self,
        execution_id: str,
        ip_address: str,
        connection_status_after: str | None,
        system_status_after: str | None,
        update_result: str | None,
        reboot_result: str | None,
        notes: str | None,
    ) -> None:
        query = """
        UPDATE dbo.affected_routers
        SET
            connection_status_after = ?,
            system_status_after = ?,
            update_result = ?,
            reboot_result = ?,
            notes = ?,
            processed_at = SYSDATETIME(),
            updated_at = SYSDATETIME()
        WHERE execution_id = ?
          AND ip_address = ?;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                connection_status_after,
                system_status_after,
                update_result,
                reboot_result,
                notes,
                execution_id,
                ip_address,
            )
            connection.commit()

    def refresh_router_status(
        self,
        execution_id: str,
        ip_address: str,
        connection_status_after: str | None,
        system_status_after: str | None,
        notes: str | None,
    ) -> None:
        query = """
        UPDATE dbo.affected_routers
        SET
            connection_status_after = ?,
            system_status_after = ?,
            notes = ?,
            updated_at = SYSDATETIME()
        WHERE execution_id = ?
          AND ip_address = ?;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                query,
                connection_status_after,
                system_status_after,
                notes,
                execution_id,
                ip_address,
            )
            connection.commit()

    def get_routers_by_execution_id(self, execution_id: str) -> list[dict[str, Any]]:
        query = """
        SELECT
            affected_id,
            execution_id,
            device_id,
            device_name,
            ip_address,
            old_location,
            new_location,
            device_type,
            connection_status_before,
            connection_status_after,
            system_status_before,
            system_status_after,
            update_result,
            reboot_result,
            notes,
            processed_at,
            created_at,
            updated_at
        FROM dbo.affected_routers
        WHERE execution_id = ?
        ORDER BY affected_id;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, execution_id)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]

    def get_ready_routers(self, execution_id: str) -> list[dict[str, Any]]:
        query = """
        SELECT
            affected_id,
            execution_id,
            device_id,
            device_name,
            ip_address,
            old_location,
            new_location,
            device_type,
            connection_status_before,
            connection_status_after,
            system_status_before,
            system_status_after,
            update_result,
            reboot_result,
            notes,
            processed_at,
            created_at,
            updated_at
        FROM dbo.affected_routers
        WHERE execution_id = ?
          AND system_status_before = 'ready'
        ORDER BY affected_id;
        """

        with self._db_manager.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query, execution_id)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]

            return [dict(zip(columns, row)) for row in rows]