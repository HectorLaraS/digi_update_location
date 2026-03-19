from __future__ import annotations

from typing import Callable

from src.services.audit_service import AuditService
from src.services.digi_service import DigiService
from src.utils.timers import sleep_seconds


class SingleRouterRebootService:
    def __init__(
        self,
        digi_service: DigiService,
        audit_service: AuditService,
        reboot_wait_after_send_seconds: int,
        reboot_poll_interval_seconds: int,
        reboot_max_check_attempts: int,
    ) -> None:
        self._digi = digi_service
        self._audit = audit_service
        self._wait_after_send = reboot_wait_after_send_seconds
        self._poll_interval = reboot_poll_interval_seconds
        self._max_attempts = reboot_max_check_attempts

    def reboot_single_router(
        self,
        execution_id: str,
        router_data: dict,
        digi_user: str | None = None,
        digi_pass: str | None = None,
        progress_callback: Callable[..., None] | None = None,
    ) -> dict:
        device_id = router_data.get("device_id")
        ip_address = router_data.get("ip_address")
        new_location = router_data.get("new_location")
        system_status_after = router_data.get("system_status_after")

        if progress_callback:
            progress_callback(
                current_phase="Preparing manual reboot",
                message=f"Preparing manual reboot for router {ip_address}.",
                attempt=0,
                max_attempts=self._max_attempts,
                countdown_seconds=None,
                countdown_label=None,
            )

        if not device_id:
            return {
                "success": False,
                "message": "Router does not have a device_id.",
            }

        if system_status_after != "updated_no_reboot":
            return {
                "success": False,
                "message": (
                    "Router is not eligible for manual reboot. "
                    "Expected status: updated_no_reboot."
                ),
            }

        if progress_callback:
            progress_callback(
                current_phase="Sending manual reboot",
                message=f"Sending manual reboot command to router {ip_address}.",
                attempt=0,
                max_attempts=self._max_attempts,
                countdown_seconds=None,
                countdown_label=None,
            )

        reboot_result = self._digi.reboot_device(
            device_id=device_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        if not reboot_result.success:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=ip_address,
                connection_status_after=None,
                system_status_after="update_failed",
                update_result="success",
                reboot_result="failed",
                notes=reboot_result.message,
            )
            self._audit.finalize_execution(execution_id)
            return {
                "success": False,
                "message": reboot_result.message,
            }

        if progress_callback:
            progress_callback(
                current_phase="Waiting after manual reboot",
                message=f"Router {ip_address} is rebooting. Waiting before reconnect checks.",
                attempt=0,
                max_attempts=self._max_attempts,
                countdown_seconds=self._wait_after_send,
                countdown_label="Waiting after reboot",
            )

        for remaining in range(self._wait_after_send, 0, -1):
            if progress_callback:
                progress_callback(
                    countdown_seconds=remaining,
                    countdown_label="Waiting after reboot",
                )
            sleep_seconds(1)

        router_reconnected = False

        for attempt in range(1, self._max_attempts + 1):
            if progress_callback:
                progress_callback(
                    current_phase="Checking reconnect status",
                    message=f"Reconnect attempt {attempt} of {self._max_attempts} for router {ip_address}.",
                    attempt=attempt,
                    max_attempts=self._max_attempts,
                    countdown_seconds=None,
                    countdown_label=None,
                )

            connection_status = self._digi.get_connection_status_by_id(
                device_id=device_id,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            if connection_status == "connected":
                router_reconnected = True
                break

            if attempt < self._max_attempts:
                if progress_callback:
                    progress_callback(
                        current_phase="Reconnect wait",
                        message=(
                            f"Router {ip_address} is still offline. "
                            f"Next reconnect attempt in {self._poll_interval} seconds."
                        ),
                        attempt=attempt,
                        max_attempts=self._max_attempts,
                        countdown_seconds=self._poll_interval,
                        countdown_label=f"Reconnect attempt {attempt}/{self._max_attempts}",
                    )

                for remaining in range(self._poll_interval, 0, -1):
                    if progress_callback:
                        progress_callback(
                            countdown_seconds=remaining,
                            countdown_label=f"Reconnect attempt {attempt}/{self._max_attempts}",
                        )
                    sleep_seconds(1)

        if not router_reconnected:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=ip_address,
                connection_status_after="disconnected",
                system_status_after="reboot_timeout",
                update_result="success",
                reboot_result="timeout",
                notes="Manual reboot timeout: router did not come back online in time.",
            )
            self._audit.finalize_execution(execution_id)
            return {
                "success": False,
                "message": "Manual reboot timeout: router did not come back online in time.",
            }

        if progress_callback:
            progress_callback(
                current_phase="Verifying location after manual reboot",
                message=f"Router {ip_address} is back online. Verifying location.",
                attempt=self._max_attempts,
                max_attempts=self._max_attempts,
                countdown_seconds=None,
                countdown_label=None,
            )

        device = self._digi.get_device_by_id(
            device_id=device_id,
            digi_user=digi_user,
            digi_pass=digi_pass,
        )

        if device is None:
            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=ip_address,
                connection_status_after="disconnected",
                system_status_after="verification_failed",
                update_result="success",
                reboot_result="success",
                notes="Router could not be retrieved from Digi after manual reboot.",
            )
            self._audit.finalize_execution(execution_id)
            return {
                "success": False,
                "message": "Router could not be retrieved from Digi after manual reboot.",
            }

        current_location = device.location or ""
        expected_location = new_location or ""

        if current_location == expected_location:
            final_status = "done"
            notes = f"Manual reboot completed successfully. Verified location: {current_location or '-'}."
            success = True
            message = "Manual reboot completed successfully."
        else:
            final_status = "verification_failed"
            notes = (
                f"Manual reboot finished but location verification failed. "
                f"Expected: {expected_location or '-'} | "
                f"Current Digi location: {current_location or '-'}."
            )
            success = False
            message = "Manual reboot finished but location verification failed."

        self._audit.update_router_execution_result(
            execution_id=execution_id,
            ip_address=ip_address,
            connection_status_after=device.connection_status,
            system_status_after=final_status,
            update_result="success",
            reboot_result="success",
            notes=notes,
        )

        self._audit.finalize_execution(execution_id)

        return {
            "success": success,
            "message": message,
        }