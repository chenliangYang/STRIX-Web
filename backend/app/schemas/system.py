"""System schemas."""

from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    """User create schema."""

    username: str
    account: str
    password: str
    role: str = "user"
    department: str | None = None


class UserUpdate(BaseModel):
    """User update schema."""

    username: str | None = None
    role: str | None = None
    department: str | None = None


class UserItem(BaseModel):
    """User item schema."""

    id: str
    username: str
    account: str
    role: str
    department: str | None = None
    status: str
    created_at: datetime
    last_login_at: datetime | None = None


class UserDetail(UserItem):
    """User detail schema."""

    updated_at: datetime | None = None


class WhitelistCreate(BaseModel):
    """Whitelist create schema."""

    name: str
    target_type: str
    target_value: str
    project: str | None = None


class WhitelistUpdate(BaseModel):
    """Whitelist update schema."""

    name: str | None = None
    target_type: str | None = None
    target_value: str | None = None
    project: str | None = None


class WhitelistItem(BaseModel):
    """Whitelist item schema."""

    id: str
    name: str
    target_type: str
    target_value: str
    target_normalized: str
    project: str | None = None
    status: str
    created_by: str
    created_at: datetime


class WhitelistDetail(WhitelistItem):
    """Whitelist detail schema."""

    updated_at: datetime | None = None


class WhitelistCheckRequest(BaseModel):
    """Whitelist check request."""

    target: str


class WhitelistCheckResponse(BaseModel):
    """Whitelist check response."""

    allowed: bool
    matched_whitelist_id: str | None = None


class AuditLogItem(BaseModel):
    """Audit log item schema."""

    id: str
    actor_id: str | None = None
    actor_account: str | None = None
    actor_role: str | None = None
    action: str
    object_type: str | None = None
    object_id: str | None = None
    request_ip: str | None = None
    result: str
    remark: str | None = None
    created_at: datetime


class DashboardSummary(BaseModel):
    """Dashboard summary schema."""

    active_projects_7d: int = 0
    total_assets_scanned: int = 0
    high_risk_vulns_30d: int = 0


class StatusDistributionItem(BaseModel):
    """Status distribution item."""

    status: str
    label: str
    count: int = 0


class RecentScanItem(BaseModel):
    """Recent scan item."""

    task_id: str
    task_name: str
    target: str
    creator: str
    created_at: datetime
    scan_status: str
    risk_level: str
