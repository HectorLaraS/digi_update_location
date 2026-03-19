from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from src.services.single_router_reboot_service import SingleRouterRebootService


@dataclass
class ManualRebootJobState:
    execution_id: str
    router_ip: str
    status: str
    message: str | None = None
    is_running: bool = False

    current_phase: str | None = None
    attempt: int = 0
    max_attempts: int = 0
    countdown_seconds: int | None = None
    countdown_label: str | None = None


class ManualRebootManager:
    def __init__(self, single_router_reboot_service: SingleRouterRebootService) -> None:
        self._single_router_reboot_service = single_router_reboot_service
        self._jobs: dict[str, ManualRebootJobState] = {}
        self._lock = threading.Lock()

    def _build_job_key(self, execution_id: str, router_ip: str) -> str:
        return f"{execution_id}::{router_ip}"

    def get_job_state(
        self,
        execution_id: str,
        router_ip: str,
    ) -> ManualRebootJobState | None:
        job_key = self._build_job_key(execution_id, router_ip)
        with self._lock:
            return self._jobs.get(job_key)

    def start_manual_reboot(
        self,
        execution_id: str,
        router_data: dict,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> ManualRebootJobState:
        router_ip = router_data.get("ip_address") or ""
        job_key = self._build_job_key(execution_id, router_ip)

        with self._lock:
            current = self._jobs.get(job_key)
            if current and current.is_running:
                return current

            job_state = ManualRebootJobState(
                execution_id=execution_id,
                router_ip=router_ip,
                status="running",
                message="Manual reboot started in background.",
                is_running=True,
                current_phase="Starting manual reboot",
            )
            self._jobs[job_key] = job_state

        thread = threading.Thread(
            target=self._run_manual_reboot,
            kwargs={
                "execution_id": execution_id,
                "router_data": router_data,
                "digi_user": digi_user,
                "digi_pass": digi_pass,
            },
            daemon=True,
        )
        thread.start()

        return job_state

    def update_progress(
        self,
        execution_id: str,
        router_ip: str,
        *,
        current_phase: str | None = None,
        attempt: int | None = None,
        max_attempts: int | None = None,
        countdown_seconds: int | None = None,
        countdown_label: str | None = None,
        message: str | None = None,
    ) -> None:
        job_key = self._build_job_key(execution_id, router_ip)

        with self._lock:
            job = self._jobs.get(job_key)
            if not job:
                return

            if current_phase is not None:
                job.current_phase = current_phase
            if attempt is not None:
                job.attempt = attempt
            if max_attempts is not None:
                job.max_attempts = max_attempts
            job.countdown_seconds = countdown_seconds
            job.countdown_label = countdown_label
            if message is not None:
                job.message = message

    def _run_manual_reboot(
        self,
        execution_id: str,
        router_data: dict,
        digi_user: str | None,
        digi_pass: str | None,
    ) -> None:
        router_ip = router_data.get("ip_address") or ""

        def progress_callback(
            *,
            current_phase: str | None = None,
            attempt: int | None = None,
            max_attempts: int | None = None,
            countdown_seconds: int | None = None,
            countdown_label: str | None = None,
            message: str | None = None,
        ) -> None:
            self.update_progress(
                execution_id=execution_id,
                router_ip=router_ip,
                current_phase=current_phase,
                attempt=attempt,
                max_attempts=max_attempts,
                countdown_seconds=countdown_seconds,
                countdown_label=countdown_label,
                message=message,
            )

        try:
            result = self._single_router_reboot_service.reboot_single_router(
                execution_id=execution_id,
                router_data=router_data,
                digi_user=digi_user,
                digi_pass=digi_pass,
                progress_callback=progress_callback,
            )

            job_key = self._build_job_key(execution_id, router_ip)
            with self._lock:
                job = self._jobs.get(job_key)
                if not job:
                    return

                job.status = "completed" if result["success"] else "failed"
                job.message = result["message"]
                job.is_running = False
                job.countdown_seconds = None
                job.countdown_label = None

                if result["success"]:
                    job.current_phase = "Manual reboot completed"
                else:
                    job.current_phase = "Manual reboot failed"

        except Exception as exc:
            job_key = self._build_job_key(execution_id, router_ip)
            with self._lock:
                job = self._jobs.get(job_key)
                if not job:
                    self._jobs[job_key] = ManualRebootJobState(
                        execution_id=execution_id,
                        router_ip=router_ip,
                        status="failed",
                        message=f"Manual reboot crashed: {exc}",
                        is_running=False,
                        current_phase="Manual reboot crashed",
                    )
                    return

                job.status = "failed"
                job.message = f"Manual reboot crashed: {exc}"
                job.is_running = False
                job.current_phase = "Manual reboot crashed"
                job.countdown_seconds = None
                job.countdown_label = None