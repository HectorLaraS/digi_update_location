from __future__ import annotations

from src.domain.router_result import RouterResult
from src.repositories.audit_repository import AuditRepository
from src.repositories.router_repository import RouterRepository


class AuditService:
    def __init__(
        self,
        audit_repository: AuditRepository,
        router_repository: RouterRepository,
    ) -> None:
        self._audit_repository = audit_repository
        self._router_repository = router_repository

    def create_execution(
        self,
        executed_by: str,
        csv_name: str | None,
        reboot_enabled: bool,
        execution_status: str = "created",
    ) -> str:
        return self._audit_repository.create_execution(
            executed_by=executed_by,
            csv_name=csv_name,
            reboot_enabled=reboot_enabled,
            execution_status=execution_status,
        )

    def save_validation_results(
        self,
        execution_id: str,
        router_results: list[RouterResult],
    ) -> None:
        ready_count = 0
        not_found_count = 0
        disconnected_count = 0

        for router_result in router_results:
            self._router_repository.insert_router_result(router_result)

            if router_result.system_status == "ready":
                ready_count += 1
            elif router_result.system_status == "not_found":
                not_found_count += 1
            elif router_result.system_status == "disconnected":
                disconnected_count += 1

        self._audit_repository.update_execution_validation_summary(
            execution_id=execution_id,
            total_rows=len(router_results),
            ready_count=ready_count,
            not_found_count=not_found_count,
            disconnected_count=disconnected_count,
            execution_status="validated",
        )

    def update_router_execution_result(
        self,
        execution_id: str,
        ip_address: str,
        connection_status_after: str | None,
        system_status_after: str | None,
        update_result: str | None,
        reboot_result: str | None,
        notes: str | None,
    ) -> None:
        self._router_repository.update_router_after_execution(
            execution_id=execution_id,
            ip_address=ip_address,
            connection_status_after=connection_status_after,
            system_status_after=system_status_after,
            update_result=update_result,
            reboot_result=reboot_result,
            notes=notes,
        )

    def finalize_execution(
        self,
        execution_id: str,
    ) -> None:
        routers = self._router_repository.get_routers_by_execution_id(execution_id)

        updated_count = 0
        rebooted_count = 0
        failed_count = 0

        for router in routers:
            update_result = router.get("update_result")
            reboot_result = router.get("reboot_result")
            system_status_after = router.get("system_status_after")

            if update_result == "success":
                updated_count += 1

            if reboot_result == "success":
                rebooted_count += 1

            if update_result == "failed" or reboot_result in {"failed", "timeout"}:
                failed_count += 1

        if failed_count > 0:
            execution_status = "completed_with_errors"
        else:
            execution_status = "completed"

        self._audit_repository.update_execution_results(
            execution_id=execution_id,
            updated_count=updated_count,
            rebooted_count=rebooted_count,
            failed_count=failed_count,
            execution_status=execution_status,
        )

    def get_execution_detail(self, execution_id: str) -> dict:
        execution = self._audit_repository.get_execution_by_id(execution_id)
        routers = self._router_repository.get_routers_by_execution_id(execution_id)

        return {
            "execution": execution,
            "routers": routers,
        }