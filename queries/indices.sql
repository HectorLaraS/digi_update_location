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