from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.domain.router_result import RouterResult
from src.services.audit_service import AuditService
from src.services.digi_service import DigiService
from src.utils.timers import poll_until, sleep_seconds


@dataclass(frozen=True)
class ExecutionOutcome:
    status: str
    paused_router_ip: str | None = None
    message: str | None = None


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
        progress_callback: Callable[..., None] | None = None,
    ) -> ExecutionOutcome:
        if reboot_enabled is None:
            reboot_enabled = self._reboot_enabled_default

        self._audit.mark_execution_running(execution_id)

        ready_routers = [router for router in routers if router.system_status == "ready"]
        total_ready = len(ready_routers)

        if progress_callback:
            progress_callback(
                current_phase="Execution started",
                processed_count=0,
                message="Execution started.",
            )

        for index, router in enumerate(ready_routers, start=1):
            if progress_callback:
                progress_callback(
                    current_phase="Processing router",
                    current_router_ip=router.ip,
                    current_router_name=router.device_name,
                    processed_count=index - 1,
                    countdown_seconds=None,
                    countdown_label=None,
                    message=f"Processing router {index} of {total_ready}.",
                )

            outcome = self._process_single_router(
                execution_id=execution_id,
                router=router,
                reboot_enabled=reboot_enabled,
                digi_user=digi_user,
                digi_pass=digi_pass,
                processed_count=index - 1,
                progress_callback=progress_callback,
            )

            if outcome is not None and outcome.status == "paused":
                self._audit.mark_execution_paused(execution_id)
                return outcome

            if progress_callback:
                progress_callback(
                    current_phase="Router completed",
                    current_router_ip=router.ip,
                    current_router_name=router.device_name,
                    processed_count=index,
                    countdown_seconds=None,
                    countdown_label=None,
                    message=f"Router {index} of {total_ready} completed.",
                )

            if reboot_enabled and index < len(ready_routers):
                if progress_callback:
                    progress_callback(
                        current_phase="Delay between routers",
                        current_router_ip=router.ip,
                        current_router_name=router.device_name,
                        processed_count=index,
                        countdown_seconds=self._delay_between,
                        countdown_label="Next router in",
                        message="Waiting before processing the next router.",
                    )

                for remaining in range(self._delay_between, 0, -1):
                    if progress_callback:
                        progress_callback(
                            countdown_seconds=remaining,
                            countdown_label="Next router in",
                        )
                    sleep_seconds(1)

                if progress_callback:
                    progress_callback(
                        countdown_seconds=None,
                        countdown_label=None,
                    )

        self._audit.finalize_execution(execution_id)

        if progress_callback:
            progress_callback(
                current_phase="Execution completed",
                processed_count=total_ready,
                countdown_seconds=None,
                countdown_label=None,
                message="Execution completed successfully.",
            )

        return ExecutionOutcome(
            status="completed",
            message="Execution completed successfully.",
        )

    def _process_single_router(
        self,
        execution_id: str,
        router: RouterResult,
        reboot_enabled: bool,
        digi_user: str | None,
        digi_pass: str | None,
        processed_count: int,
        progress_callback: Callable[..., None] | None = None,
    ) -> ExecutionOutcome | None:
        if progress_callback:
            progress_callback(
                current_phase="Updating location",
                current_router_ip=router.ip,
                current_router_name=router.device_name,
                processed_count=processed_count,
                message=f"Updating location for router {router.ip}.",
            )

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
            return None

        if not reboot_enabled:
            if progress_callback:
                progress_callback(
                    current_phase="Verifying location",
                    current_router_ip=router.ip,
                    current_router_name=router.device_name,
                    processed_count=processed_count,
                    message=f"Verifying location for router {router.ip}.",
                )

            self._finalize_router_with_location_verification(
                execution_id=execution_id,
                router=router,
                reboot_result="skipped",
                success_message="Location updated without reboot.",
                digi_user=digi_user,
                digi_pass=digi_pass,
            )
            return None

        if progress_callback:
            progress_callback(
                current_phase="Sending reboot",
                current_router_ip=router.ip,
                current_router_name=router.device_name,
                processed_count=processed_count,
                message=f"Sending reboot command to router {router.ip}.",
            )

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
            return None

        if progress_callback:
            progress_callback(
                current_phase="Waiting after reboot",
                current_router_ip=router.ip,
                current_router_name=router.device_name,
                processed_count=processed_count,
                countdown_seconds=self._wait_after_send,
                countdown_label="Waiting after reboot",
                message=f"Waiting after reboot for router {router.ip}.",
            )

        for remaining in range(self._wait_after_send, 0, -1):
            if progress_callback:
                progress_callback(
                    countdown_seconds=remaining,
                    countdown_label="Waiting after reboot",
                )
            sleep_seconds(1)

        if progress_callback:
            progress_callback(
                current_phase="Polling reconnect",
                current_router_ip=router.ip,
                current_router_name=router.device_name,
                processed_count=processed_count,
                countdown_seconds=None,
                countdown_label=None,
                message=f"Polling reconnect status for router {router.ip}.",
            )

        success = self._poll_router_reconnect(
            router=router,
            digi_user=digi_user,
            digi_pass=digi_pass,
            processed_count=processed_count,
            progress_callback=progress_callback,
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
            return ExecutionOutcome(
                status="paused",
                paused_router_ip=router.ip,
                message=(
                    f"Execution paused because router {router.ip} "
                    f"did not come back online in time."
                ),
            )

        if progress_callback:
            progress_callback(
                current_phase="Verifying location",
                current_router_ip=router.ip,
                current_router_name=router.device_name,
                processed_count=processed_count,
                message=f"Verifying location for router {router.ip}.",
            )

        self._finalize_router_with_location_verification(
            execution_id=execution_id,
            router=router,
            reboot_result="success",
            success_message="Reboot completed successfully.",
            digi_user=digi_user,
            digi_pass=digi_pass,
        )
        return None

    def _poll_router_reconnect(
        self,
        router: RouterResult,
        digi_user: str | None,
        digi_pass: str | None,
        processed_count: int,
        progress_callback: Callable[..., None] | None = None,
    ) -> bool:
        for attempt in range(1, self._max_attempts + 1):
            is_connected = self._is_router_connected(
                device_id=router.device_id,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            if is_connected:
                return True

            if attempt < self._max_attempts:
                if progress_callback:
                    progress_callback(
                        current_phase="Polling reconnect",
                        current_router_ip=router.ip,
                        current_router_name=router.device_name,
                        processed_count=processed_count,
                        countdown_seconds=self._poll_interval,
                        countdown_label=f"Reconnect check {attempt}/{self._max_attempts}",
                        message=(
                            f"Router {router.ip} is still offline. "
                            f"Next reconnect check in {self._poll_interval} seconds."
                        ),
                    )

                for remaining in range(self._poll_interval, 0, -1):
                    if progress_callback:
                        progress_callback(
                            countdown_seconds=remaining,
                            countdown_label=f"Reconnect check {attempt}/{self._max_attempts}",
                        )
                    sleep_seconds(1)

        if progress_callback:
            progress_callback(
                countdown_seconds=None,
                countdown_label=None,
            )

        return False

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
            notes = f"{success_message} Verified location: {current_location or '-'}."
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