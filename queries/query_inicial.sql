CREATE DATABASE DigiLocationManager
COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

CREATE DATABASE DigiLocationManager
ON PRIMARY (
    NAME = DigiLocationManager_Data,
    FILENAME = 'C:\SQLData\DigiLocationManager_Data.mdf',
    SIZE = 100MB,
    FILEGROWTH = 50MB
)
LOG ON (
    NAME = DigiLocationManager_Log,
    FILENAME = 'C:\SQLData\DigiLocationManager_Log.ldf',
    SIZE = 50MB,
    FILEGROWTH = 25MB
)
COLLATE SQL_Latin1_General_CP1_CI_AS;
GO

CREATE INDEX IX_affected_routers_execution_id
ON dbo.affected_routers(execution_id);
GO

CREATE INDEX IX_affected_routers_ip_address
ON dbo.affected_routers(ip_address);
GO

CREATE INDEX IX_affected_routers_device_id
ON dbo.affected_routers(device_id);
GO

CREATE INDEX IX_audit_log_started_at
ON dbo.audit_log(started_at);
GO