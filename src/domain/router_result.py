from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouterResult:
    execution_id: str
    ip: str
    new_location: str
    device_id: str | None = None
    device_name: str | None = None
    old_location: str | None = None
    device_type: str | None = None
    connection_status: str | None = None
    system_status: str | None = None
    message: str | None = None

    def __str__(self) -> str:
        return (
            f"{self.ip} | old={self.old_location} | new={self.new_location} | "
            f"status={self.system_status} | msg={self.message}"
        )