from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

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

            job_state = ExecutionJobState(
                execution_id=execution_id,
                status="running",
                message="Execution continue started in background.",
                is_running=True,
                is_cancel_requested=False,
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

    def _run_execution(
        self,
        execution_id: str,
        routers: list[RouterResult],
        reboot_enabled: bool | None,
        digi_user: str | None,
        digi_pass: str | None,
    ) -> None:
        try:
            outcome: ExecutionOutcome = self._execution_service.execute(
                execution_id=execution_id,
                routers=routers,
                reboot_enabled=reboot_enabled,
                digi_user=digi_user,
                digi_pass=digi_pass,
            )

            with self._lock:
                job = self._jobs.get(execution_id)
                if not job:
                    return

                job.status = outcome.status
                job.message = outcome.message
                job.paused_router_ip = outcome.paused_router_ip
                job.is_running = False

        except Exception as exc:
            with self._lock:
                job = self._jobs.get(execution_id)
                if not job:
                    self._jobs[execution_id] = ExecutionJobState(
                        execution_id=execution_id,
                        status="failed",
                        message=f"Execution crashed: {exc}",
                        is_running=False,
                    )
                    return

                job.status = "failed"
                job.message = f"Execution crashed: {exc}"
                job.is_running = False