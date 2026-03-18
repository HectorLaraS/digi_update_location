USE master;
GO

CREATE DATABASE DigiLocationManager


USE DigiLocationManager;
GO

CREATE TABLE dbo.audit_log (
    audit_id               BIGINT IDENTITY(1,1) PRIMARY KEY,
    execution_id           UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    executed_by            NVARCHAR(100) NOT NULL,
    started_at             DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
    finished_at            DATETIME2(0) NULL,
    csv_name               NVARCHAR(260) NULL,
    total_rows             INT NOT NULL DEFAULT 0,
    ready_count            INT NOT NULL DEFAULT 0,
    not_found_count        INT NOT NULL DEFAULT 0,
    disconnected_count     INT NOT NULL DEFAULT 0,
    updated_count          INT NOT NULL DEFAULT 0,
    rebooted_count         INT NOT NULL DEFAULT 0,
    failed_count           INT NOT NULL DEFAULT 0,
    reboot_enabled         BIT NOT NULL DEFAULT 1,
    execution_status       NVARCHAR(30) NOT NULL DEFAULT 'created',
    created_at             DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
    updated_at             DATETIME2(0) NOT NULL DEFAULT SYSDATETIME()
);
GO

ALTER TABLE dbo.audit_log
ADD CONSTRAINT UQ_audit_log_execution_id UNIQUE (execution_id);
GO

ALTER TABLE dbo.audit_log
ADD CONSTRAINT CK_audit_log_execution_status
CHECK (execution_status IN (
    'created',
    'validated',
    'running',
    'paused',
    'completed',
    'completed_with_errors',
    'failed',
    'cancelled'
));
GO

CREATE TABLE dbo.affected_routers (
    affected_id                 BIGINT IDENTITY(1,1) PRIMARY KEY,
    execution_id                UNIQUEIDENTIFIER NOT NULL,
    device_id                   NVARCHAR(100) NULL,
    device_name                 NVARCHAR(200) NULL,
    ip_address                  VARCHAR(50) NOT NULL,
    old_location                NVARCHAR(255) NULL,
    new_location                NVARCHAR(255) NULL,
    device_type                 NVARCHAR(150) NULL,
    connection_status_before    NVARCHAR(30) NULL,
    connection_status_after     NVARCHAR(30) NULL,
    system_status_before        NVARCHAR(50) NULL,
    system_status_after         NVARCHAR(50) NULL,
    update_result               NVARCHAR(30) NULL,
    reboot_result               NVARCHAR(30) NULL,
    notes                       NVARCHAR(1000) NULL,
    processed_at                DATETIME2(0) NULL,
    created_at                  DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
    updated_at                  DATETIME2(0) NOT NULL DEFAULT SYSDATETIME()
);
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT FK_affected_routers_execution_id
FOREIGN KEY (execution_id) REFERENCES dbo.audit_log(execution_id);
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_connection_status_before
CHECK (connection_status_before IS NULL OR connection_status_before IN ('connected', 'disconnected'));
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_connection_status_after
CHECK (connection_status_after IS NULL OR connection_status_after IN ('connected', 'disconnected'));
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_system_status_before
CHECK (system_status_before IS NULL OR system_status_before IN (
    'ready',
    'not_found',
    'disconnected',
    'pending_reboot',
    'updated_no_reboot',
    'rebooting',
    'reboot_timeout',
    'update_failed',
    'done'
));
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_system_status_after
CHECK (system_status_after IS NULL OR system_status_after IN (
    'ready',
    'not_found',
    'disconnected',
    'pending_reboot',
    'updated_no_reboot',
    'rebooting',
    'reboot_timeout',
    'update_failed',
    'done'
));
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_update_result
CHECK (update_result IS NULL OR update_result IN (
    'pending',
    'skipped',
    'success',
    'failed'
));
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_reboot_result
CHECK (reboot_result IS NULL OR reboot_result IN (
    'pending',
    'skipped',
    'success',
    'timeout',
    'failed'
));
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

----------------------------------

USE DigiLocationManager;
GO

ALTER TABLE dbo.affected_routers
DROP CONSTRAINT CK_affected_routers_system_status_before;
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_system_status_before
CHECK (system_status_before IS NULL OR system_status_before IN (
    'ready',
    'not_found',
    'disconnected',
    'pending_reboot',
    'updated_no_reboot',
    'rebooting',
    'reboot_timeout',
    'update_failed',
    'verification_failed',
    'done'
));
GO

ALTER TABLE dbo.affected_routers
DROP CONSTRAINT CK_affected_routers_system_status_after;
GO

ALTER TABLE dbo.affected_routers
ADD CONSTRAINT CK_affected_routers_system_status_after
CHECK (system_status_after IS NULL OR system_status_after IN (
    'ready',
    'not_found',
    'disconnected',
    'pending_reboot',
    'updated_no_reboot',
    'rebooting',
    'reboot_timeout',
    'update_failed',
    'verification_failed',
    'done'
));
GO