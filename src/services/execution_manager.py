from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from src.domain.router_result import RouterResult
from src.services.execution_service import ExecutionOutcome, ExecutionService


@dataclass
class ExecutionJobState:
    execution_id: str
    status: str
    message: str | None = None
    paused_router_ip: str | None = None
    is_running: bool = False
    is_cancel_requested: bool = False

    current_phase: str | None = None
    current_router_ip: str | None = None
    current_router_name: str | None = None
    processed_count: int = 0
    total_count: int = 0
    countdown_seconds: int | None = None
    countdown_label: str | None = None


class ExecutionManager:
    def __init__(self, execution_service: ExecutionService) -> None:
        self._execution_service = execution_service
        self._jobs: dict[str, ExecutionJobState] = {}
        self._lock = threading.Lock()

    def get_job_state(self, execution_id: str) -> ExecutionJobState | None:
        with self._lock:
            return self._jobs.get(execution_id)

    def start_execution(
        self,
        execution_id: str,
        routers: list[RouterResult],
        reboot_enabled: bool | None = None,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> ExecutionJobState:
        with self._lock:
            current = self._jobs.get(execution_id)
            if current and current.is_running:
                return current

            job_state = ExecutionJobState(
                execution_id=execution_id,
                status="running",
                message="Execution started in background.",
                is_running=True,
                is_cancel_requested=False,
                current_phase="Starting execution",
                processed_count=0,
                total_count=len([router for router in routers if router.system_status == "ready"]),
            )
            self._jobs[execution_id] = job_state

        thread = threading.Thread(
            target=self._run_execution,
            kwargs={
                "execution_id": execution_id,
                "routers": routers,
                "reboot_enabled": reboot_enabled,
                "digi_user": digi_user,
                "digi_pass": digi_pass,
            },
            daemon=True,
        )
        thread.start()

        return job_state

    def continue_execution(
        self,
        execution_id: str,
        routers: list[RouterResult],
        reboot_enabled: bool | None = None,
        digi_user: str | None = None,
        digi_pass: str | None = None,
    ) -> ExecutionJobState:
        with self._lock:
            current = self._jobs.get(execution_id)
            if current and current.is_running:
                return current

            already_processed = 0
            existing = self._jobs.get(execution_id)
            if existing:
                already_processed = existing.processed_count

            total_ready = already_processed + len(routers)

            job_state = ExecutionJobState(
                execution_id=execution_id,
                status="running",
                message="Execution continue started in background.",
                is_running=True,
                is_cancel_requested=False,
                current_phase="Continuing execution",
                processed_count=already_processed,
                total_count=total_ready,
            )
            self._jobs[execution_id] = job_state

        thread = threading.Thread(
            target=self._run_execution,
            kwargs={
                "execution_id": execution_id,
                "routers": routers,
                "reboot_enabled": reboot_enabled,
                "digi_user": digi_user,
                "digi_pass": digi_pass,
            },
            daemon=True,
        )
        thread.start()

        return job_state

    def request_cancel(self, execution_id: str) -> None:
        with self._lock:
            job = self._jobs.get(execution_id)
            if job:
                job.is_cancel_requested = True
                job.status = "cancel_requested"
                job.message = "Cancellation requested."
                job.current_phase = "Cancellation requested"

    def update_progress(
        self,
        execution_id: str,
        *,
        current_phase: str | None = None,
        current_router_ip: str | None = None,
        current_router_name: str | None = None,
        processed_count: int | None = None,
        countdown_seconds: int | None = None,
        countdown_label: str | None = None,
        message: str | None = None,
    ) -> None:
        with self._lock:
            job = self._jobs.get(execution_id)
            if not job:
                return

            if current_phase is not None:
                job.current_phase = current_phase
            if current_router_ip is not None:
                job.current_router_ip = current_router_ip
            if current_router_name is not None:
                job.current_router_name = current_router_name
            if processed_count is not None:
                job.processed_count = processed_count
            if countdown_seconds is not None or countdown_seconds is None:
                job.countdown_seconds = countdown_seconds
            if countdown_label is not None or countdown_label is None:
                job.countdown_label = countdown_label
            if message is not None:
                job.message = message

    def clear_countdown(self, execution_id: str) -> None:
        with self._lock:
            job = self._jobs.get(execution_id)
            if not job:
                return
            job.countdown_seconds = None
            job.countdown_label = None

    def _run_execution(
        self,
        execution_id: str,
        routers: list[RouterResult],
        reboot_enabled: bool | None,
        digi_user: str | None,
        digi_pass: str | None,
    ) -> None:
        def progress_callback(
            *,
            current_phase: str | None = None,
            current_router_ip: str | None = None,
            current_router_name: str | None = None,
            processed_count: int | None = None,
            countdown_seconds: int | None = None,
            countdown_label: str | None = None,
            message: str | None = None,
        ) -> None:
            self.update_progress(
                execution_id=execution_id,
                current_phase=current_phase,
                current_router_ip=current_router_ip,
                current_router_name=current_router_name,
                processed_count=processed_count,
                countdown_seconds=countdown_seconds,
                countdown_label=countdown_label,
                message=message,
            )

        try:
            outcome: ExecutionOutcome = self._execution_service.execute(
                execution_id=execution_id,
                routers=routers,
                reboot_enabled=reboot_enabled,
                digi_user=digi_user,
                digi_pass=digi_pass,
                progress_callback=progress_callback,
            )

            with self._lock:
                job = self._jobs.get(execution_id)
                if not job:
                    return

                job.status = outcome.status
                job.message = outcome.message
                job.paused_router_ip = outcome.paused_router_ip
                job.is_running = False
                job.countdown_seconds = None
                job.countdown_label = None

                if outcome.status == "completed":
                    job.current_phase = "Execution completed"
                elif outcome.status == "paused":
                    job.current_phase = "Execution paused"
                    job.current_router_ip = outcome.paused_router_ip
                elif outcome.status == "failed":
                    job.current_phase = "Execution failed"

        except Exception as exc:
            with self._lock:
                job = self._jobs.get(execution_id)
                if not job:
                    self._jobs[execution_id] = ExecutionJobState(
                        execution_id=execution_id,
                        status="failed",
                        message=f"Execution crashed: {exc}",
                        is_running=False,
                        current_phase="Execution crashed",
                    )
                    return

                job.status = "failed"
                job.message = f"Execution crashed: {exc}"
                job.is_running = False
                job.current_phase = "Execution crashed"
                job.countdown_seconds = None
                job.countdown_label = None