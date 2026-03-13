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