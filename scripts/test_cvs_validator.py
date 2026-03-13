from pathlib import Path

from src.services.csv_service import CsvService
from src.services.validation_service import ValidationService

csv_service = CsvService()
validation_service = ValidationService()

rows = csv_service.load_rows(Path("prueba_1.csv"))
print("Loaded rows:")
for row in rows:
    print(row)

result = validation_service.validate_rows(rows)

print("\nValid rows:")
for row in result.valid_rows:
    print(row)

print("\nErrors:")
for error in result.errors:
    print(error)

print("\nIs valid:", result.is_valid)