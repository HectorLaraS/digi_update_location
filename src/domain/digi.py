from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Digi:
    id: str | None = None
    customer_id: str | None = None
    d_type: str | None = None
    description: str | None = None
    ip: str | None = None
    name: str | None = None
    location: str | None = None
    connection_status: str | None = None

    def __str__(self) -> str:
        return (
            f"{self.name} | {self.ip} | {self.location} | "
            f"{self.connection_status} | {self.id}"
        )