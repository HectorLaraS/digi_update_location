from __future__ import annotations

from dataclasses import dataclass

import pyodbc

from src.config.settings import Settings


@dataclass(frozen=True)
class DatabaseConfig:
    server: str
    database: str
    username: str
    password: str
    driver: str
    trust_server_certificate: bool


class DatabaseManager:
    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config

    def build_connection_string(self) -> str:
        trust_cert = "yes" if self._config.trust_server_certificate else "no"

        return (
            f"DRIVER={{{self._config.driver}}};"
            f"SERVER={self._config.server};"
            f"DATABASE={self._config.database};"
            f"UID={self._config.username};"
            f"PWD={self._config.password};"
            f"TrustServerCertificate={trust_cert};"
        )

    def get_connection(self) -> pyodbc.Connection:
        connection_string = self.build_connection_string()
        return pyodbc.connect(connection_string)

    def test_connection(self) -> str:
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT DB_NAME() AS current_database;")
            row = cursor.fetchone()
            return str(row[0]) if row else ""


def build_database_manager(settings: Settings) -> DatabaseManager:
    config = DatabaseConfig(
        server=settings.db_server,
        database=settings.db_database,
        username=settings.db_username,
        password=settings.db_password,
        driver=settings.db_driver,
        trust_server_certificate=settings.db_trust_server_certificate,
    )
    return DatabaseManager(config)