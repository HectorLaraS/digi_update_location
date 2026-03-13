from __future__ import annotations

from pathlib import Path

from src.domain.csv_row import CsvRow
from src.utils.csv_loader import load_csv


class CsvService:
    def load_rows(self, file_path: Path) -> list[CsvRow]:
        return load_csv(file_path)