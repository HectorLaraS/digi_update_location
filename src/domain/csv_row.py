from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CsvRow:
    ip: str
    new_location: str

    def __str__(self) -> str:
        return f"{self.ip} -> {self.new_location}"