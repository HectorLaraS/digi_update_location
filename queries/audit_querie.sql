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