from __future__ import annotations

from src.domain.router_result import RouterResult
from src.services.audit_service import AuditService
from src.services.digi_service import DigiService
from src.utils.timers import poll_until, sleep_seconds


class ExecutionService:
    def __init__(
        self,
        digi_service: DigiService,
        audit_service: AuditService,
        reboot_enabled_default: bool,
        reboot_wait_after_send_seconds: int,
        reboot_poll_interval_seconds: int,
        reboot_max_check_attempts: int,
        reboot_delay_between_routers_seconds: int,
    ) -> None:
        self._digi = digi_service
        self._audit = audit_service

        self._reboot_enabled_default = reboot_enabled_default
        self._wait_after_send = reboot_wait_after_send_seconds
        self._poll_interval = reboot_poll_interval_seconds
        self._max_attempts = reboot_max_check_attempts
        self._delay_between = reboot_delay_between_routers_seconds

    def execute(
        self,
        execution_id: str,
        routers: list[RouterResult],
        reboot_enabled: bool | None = None,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> None:
        if reboot_enabled is None:
            reboot_enabled = self._reboot_enabled_default

        ready_routers = [router for router in routers if router.system_status == "ready"]

        for index, router in enumerate(ready_routers, start=1):
            self._process_single_router(
                execution_id=execution_id,
                router=router,
                reboot_enabled=reboot_enabled,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            if reboot_enabled and index < len(ready_routers):
                sleep_seconds(self._delay_between)

        self._audit.finalize_execution(execution_id)

    def _process_single_router(
        self,
        execution_id: str,
        router: RouterResult,
        reboot_enabled: bool,
        digi_user: str | None,
        digi_pass: str | None,
    ) -> None:
        update_result = self._digi.update_system_location(
            device_id=router.device_id,
            new_location=router.new_location,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        if not update_result.success:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=router.ip,
                connection_status_after=None,
                system_status_after="update_failed",
                update_result="failed",
                reboot_result="skipped",
                notes=update_result.message,
            )
            return

        if not reboot_enabled:
            self._finalize_router_with_location_verification(
                execution_id=execution_id,
                router=router,
                reboot_result="skipped",
                success_message="Location updated without reboot.",
                digi_user=digi_user,
                digi_pass=digi_pass,
            )
            return

        reboot_result = self._digi.reboot_device(
            device_id=router.device_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        if not reboot_result.success:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=router.ip,
                connection_status_after=None,
                system_status_after="update_failed",
                update_result="success",
                reboot_result="failed",
                notes=reboot_result.message,
            )
            return

        sleep_seconds(self._wait_after_send)

        success = poll_until(
            lambda: self._is_router_connected(
                device_id=router.device_id,
                digi_user=digi_user,
                digi_pass=digi_pass,
            ),
            interval_seconds=self._poll_interval,
            max_attempts=self._max_attempts,
        )

        if not success:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=router.ip,
                connection_status_after="disconnected",
                system_status_after="reboot_timeout",
                update_result="success",
                reboot_result="timeout",
                notes="Router did not come back online in time.",
            )
            return

        self._finalize_router_with_location_verification(
            execution_id=execution_id,
            router=router,
            reboot_result="success",
            success_message="Reboot completed successfully.",
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

    def _finalize_router_with_location_verification(
        self,
        execution_id: str,
        router: RouterResult,
        reboot_result: str,
        success_message: str,
        digi_user: str | None,
        digi_pass: str | None,
    ) -> None:
        device = self._digi.get_device_by_id(
            device_id=router.device_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        if device is None:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=router.ip,
                connection_status_after="disconnected",
                system_status_after="verification_failed",
                update_result="success",
                reboot_result=reboot_result,
                notes="Router could not be retrieved from Digi for location verification.",
            )
            return

        current_location = device.location or ""
        expected_location = router.new_location or ""

        if current_location == expected_location:
            final_status = "updated_no_reboot" if reboot_result == "skipped" else "done"
            notes = (
                f"{success_message} Verified location: {current_location or '-'}."
            )
        else:
            final_status = "verification_failed"
            notes = (
                f"Location verification failed. Expected: {expected_location or '-'} | "
                f"Current Digi location: {current_location or '-'}."
            )

        self._audit.update_router_execution_result(
            execution_id=execution_id,
            ip_address=router.ip,
            connection_status_after=device.connection_status,
            system_status_after=final_status,
            update_result="success",
            reboot_result=reboot_result,
            notes=notes,
        )

    def _is_router_connected(
        self,
        device_id: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> bool:
        status = self._digi.get_connection_status_by_id(
            device_id=device_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )
        return status == "connected"