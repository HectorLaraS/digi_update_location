from src.config.settings import settings
from src.repositories.db import build_database_manager
from src.repositories.audit_repository import AuditRepository

db_manager = build_database_manager(settings)
audit_repo = AuditRepository(db_manager)

execution_id = audit_repo.create_execution(
    executed_by="hector",
    csv_name="test.csv",
    reboot_enabled=True,
)

print("Execution ID:", execution_id)

audit_repo.update_execution_validation_summary(
    execution_id=execution_id,
    total_rows=10,
    ready_count=7,
    not_found_count=2,
    disconnected_count=1,
)

execution = audit_repo.get_execution_by_id(execution_id)
print(execution)

from src.domain.router_result import RouterResult
from src.repositories.router_repository import RouterRepository

router_repo = RouterRepository(db_manager)

router = RouterResult(
    execution_id=execution_id,
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

router_repo.insert_router_result(router)

routers = router_repo.get_routers_by_execution_id(execution_id)
print(routers)

from src.domain.router_result import RouterResult
from src.repositories.router_repository import RouterRepository

router_repo = RouterRepository(db_manager)

router = RouterResult(
    execution_id=execution_id,
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

router_repo.insert_router_result(router)

routers = router_repo.get_routers_by_execution_id(execution_id)
print(routers)