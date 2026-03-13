from src.utils.validators import is_valid_ipv4

print(is_valid_ipv4("10.199.35.246"))
print(is_valid_ipv4("999.1.1.1"))

from pathlib import Path
from src.utils.csv_loader import load_csv

rows = load_csv(Path("test_2.csv"))
print(rows)

from src.utils.timers import poll_until

counter = {"n": 0}

def condition():
    counter["n"] += 1
    return counter["n"] >= 3

print(poll_until(condition, interval_seconds=1, max_attempts=5))