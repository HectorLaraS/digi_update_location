from __future__ import annotations

from src.services.audit_service import AuditService
from src.services.digi_service import DigiService


class RefreshService:
    def __init__(
        self,
        digi_service: DigiService,
        audit_service: AuditService,
    ) -> None:
        self._digi = digi_service
        self._audit = audit_service

    def refresh_execution(
        self,
        execution_id: str,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> dict:
        detail = self._audit.get_execution_detail(execution_id)
        routers = detail["routers"]

        for router in routers:
            device_id = router.get("device_id")
            ip_address = router.get("ip_address")
            new_location = router.get("new_location")
            system_status_before = router.get("system_status_before")
            system_status_after = router.get("system_status_after")
            update_result = router.get("update_result")
            reboot_result = router.get("reboot_result")
            current_notes = router.get("notes")

            if not device_id:
                continue

            device = self._digi.get_device_by_id(
                device_id=device_id,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            if device is None:
                refreshed_connection_status = "disconnected"
                refreshed_system_status = "verification_failed"
                refreshed_notes = "Refresh could not retrieve the router from Digi."
            else:
                refreshed_connection_status = device.connection_status
                current_location = device.location or ""
                expected_location = new_location or ""

                if device.connection_status == "connected":
                    if current_location == expected_location:
                        if system_status_after == "updated_no_reboot":
                            refreshed_system_status = "updated_no_reboot"
                        else:
                            refreshed_system_status = "done"
                        refreshed_notes = (
                            f"Refresh verified location successfully. "
                            f"Current Digi location: {current_location or '-'} | "
                            f"Current Digi status: {device.connection_status or '-'}"
                        )
                    else:
                        refreshed_system_status = "verification_failed"
                        refreshed_notes = (
                            f"Refresh location verification failed. "
                            f"Expected: {expected_location or '-'} | "
                            f"Current Digi location: {current_location or '-'} | "
                            f"Current Digi status: {device.connection_status or '-'}"
                        )
                else:
                    if system_status_after in {"done", "updated_no_reboot"}:
                        refreshed_system_status = "disconnected"
                    else:
                        refreshed_system_status = (
                            system_status_after
                            or system_status_before
                            or "disconnected"
                        )

                    refreshed_notes = (
                        f"Current Digi location: {current_location or '-'} | "
                        f"Current Digi status: {device.connection_status or '-'}"
                    )

            if current_notes:
                refreshed_notes = f"{current_notes} | {refreshed_notes}"

            self._audit.update_router_execution_result(
                execution_id=execution_id,
                ip_address=ip_address,
                connection_status_after=refreshed_connection_status,
                system_status_after=refreshed_system_status,
                update_result=update_result,
                reboot_result=reboot_result,
                notes=refreshed_notes,
            )

        return self._audit.get_execution_detail(execution_id)