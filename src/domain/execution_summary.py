from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionSummary:
    execution_id: str
    total_rows: int
    ready_count: int
    not_found_count: int
    disconnected_count: int
    updated_count: int = 0
    rebooted_count: int = 0
    failed_count: int = 0
    execution_status: str = "created"

    def __str__(self) -> str:
        return (
            f"Execution {self.execution_id} | total={self.total_rows} | "
            f"ready={self.ready_count} | not_found={self.not_found_count} | "
            f"disconnected={self.disconnected_count} | status={self.execution_status}"
        )