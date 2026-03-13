from src.config.settings import settings
from src.domain.router_result import RouterResult
from src.repositories.audit_repository import AuditRepository
from src.repositories.db import build_database_manager
from src.repositories.router_repository import RouterRepository
from src.services.audit_service import AuditService

db_manager = build_database_manager(settings)
audit_repository = AuditRepository(db_manager)
router_repository = RouterRepository(db_manager)

audit_service = AuditService(
    audit_repository=audit_repository,
    router_repository=router_repository,
)

execution_id = audit_service.create_execution(
    executed_by="hector",
    csv_name="test.csv",
    reboot_enabled=True,
)

routers = [
    RouterResult(
        execution_id=execution_id,
        ip="172.16.2.10",
        new_location="cprs:w999999cell9",
        device_id="device-001",
        device_name="TX54-A",
        old_location="cprs:old001",
        device_type="transport",
        connection_status="connected",
        system_status="ready",
        message="Router is ready for update.",
    ),
    RouterResult(
        execution_id=execution_id,
        ip="10.1.1.20",
        new_location="cprs:w888888cell2",
        device_id=None,
        device_name=None,
        old_location=None,
        device_type=None,
        connection_status=None,
        system_status="not_found",
        message="Router was not found in Digi.",
    ),
]

audit_service.save_validation_results(
    execution_id=execution_id,
    router_results=routers,
)

audit_service.update_router_execution_result(
    execution_id=execution_id,
    ip_address="172.16.2.10",
    connection_status_after="connected",
    system_status_after="done",
    update_result="success",
    reboot_result="success",
    notes="Location updated and reboot completed successfully.",
)

audit_service.finalize_execution(execution_id)

detail = audit_service.get_execution_detail(execution_id)
print(detail["execution"])
print(detail["routers"])