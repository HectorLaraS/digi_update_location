from __future__ import annotations

from dataclasses import dataclass

from src.domain.csv_row import CsvRow
from src.utils.validators import is_valid_ipv4, is_valid_location


@dataclass(frozen=True)
class ValidationError:
    row_number: int
    ip: str
    message: str

    def __str__(self) -> str:
        return f"Row {self.row_number} | IP={self.ip} | {self.message}"


@dataclass(frozen=True)
class ValidationResult:
    valid_rows: list[CsvRow]
    errors: list[ValidationError]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class ValidationService:
    def validate_rows(self, rows: list[CsvRow]) -> ValidationResult:
        valid_rows: list[CsvRow] = []
        errors: list[ValidationError] = []
        seen_ips: set[str] = set()

        for index, row in enumerate(rows, start=1):
            row_errors: list[str] = []

            if not is_valid_ipv4(row.ip):
                row_errors.append("Invalid IPv4 address.")

            if not is_valid_location(row.new_location):
                row_errors.append("New location is empty or invalid.")

            if row.ip in seen_ips:
                row_errors.append("Duplicate IP detected in CSV.")

            if row_errors:
                errors.append(
                    ValidationError(
                        row_number=index,
                        ip=row.ip,
                        message=" ".join(row_errors),
                    )
                )
                continue

            seen_ips.add(row.ip)
            valid_rows.append(row)

        return ValidationResult(valid_rows=valid_rows, errors=errors)