from src.config.settings import settings

print("APP_HOST:", settings.app_host)
print("APP_PORT:", settings.app_port)
print("APP_DEBUG:", settings.app_debug)

print("DIGI_BASE_URL:", settings.digi_base_url)
print("DIGI_SEARCH_NODE_BY_ID:", settings.digi_search_node_by_id)
print(f"FULL URL SEARCH BY ID: {settings.digi_base_url}/{settings.digi_search_node_by_id}")
print("DIGI_TIMEOUT_SECONDS:", settings.digi_timeout_seconds)

print("DB_SERVER:", settings.db_server)
print("DB_DATABASE:", settings.db_database)
print("DB_DRIVER:", settings.db_driver)

print("LOG_PATH:", settings.log_path)

print(type(settings.digi_timeout_seconds))
print(type(settings.reboot_enabled_default))
print(type(settings.app_debug))