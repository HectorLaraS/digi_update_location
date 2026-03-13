from src.config.settings import settings
from src.services.digi_service import DigiService

digi_service = DigiService(settings)

device = digi_service.search_device_by_ip("10.199.35.246")
print(device)

device = digi_service.get_device_by_id("00000000-00000000-0040FFFF-FF1700F0")
print(device)

status = digi_service.get_connection_status_by_id("00000000-00000000-0040FFFF-FF1700F0")
print("Connection status:", status)