from __future__ import annotations

import csv
from pathlib import Path

from src.domain.csv_row import CsvRow
from src.utils.validators import normalize_string


def load_csv(file_path: Path) -> list[CsvRow]:
    rows: list[CsvRow] = []

    with file_path.open(mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for raw_row in reader:
            ip = normalize_string(raw_row.get("ip"))
            new_location = normalize_string(raw_row.get("new_location"))

            if not ip and not new_location:
                continue  # fila vacía

            rows.append(CsvRow(ip=ip, new_location=new_location))

    return rows