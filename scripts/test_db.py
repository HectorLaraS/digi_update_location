from src.config.settings import settings
from src.repositories.db import build_database_manager

db_manager = build_database_manager(settings)

print("Connection string created successfully.")
print("Database detected:", db_manager.test_connection())