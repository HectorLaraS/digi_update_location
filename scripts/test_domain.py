from src.domain.csv_row import CsvRow
from src.domain.digi import Digi
from src.domain.execution_summary import ExecutionSummary
from src.domain.router_result import RouterResult

row = CsvRow(ip="172.16.2.10", new_location="cprs:w999999cell9")
print(row)

device = Digi(
    id="00000000-00000000-0040FFFF-FF1700F0",
    ip="172.16.2.10",
    name="TX54-Test",
    location="cprs:w123456cell1",
    connection_status="connected",
)
print(device)

summary = ExecutionSummary(
    execution_id="test-exec-001",
    total_rows=10,
    ready_count=7,
    not_found_count=2,
    disconnected_count=1,
    execution_status="validated",
)
print(summary)

result = RouterResult(
    execution_id="test-exec-001",
    ip="172.16.2.10",
    new_location="cprs:w999999cell9",
    device_id="00000000-00000000-0040FFFF-FF1700F0",
    device_name="TX54-Test",
    old_location="cprs:w123456cell1",
    device_type="transport",
    connection_status="connected",
    system_status="ready",
    message="Router is ready for update.",
)
print(result)