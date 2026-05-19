"""Task schemas."""

from datetime import datetime

from pydantic import BaseModel


class TaskCreate(BaseModel):
    """Task create schema."""

    name: str
    target: str
    scan_mode: str = "standard"
    interactive: bool = False
    instruction: str | None = None


class TaskUpdate(BaseModel):
    """Task update schema."""

    name: str | None = None
    target: str | None = None
    scan_mode: str | None = None
    interactive: bool | None = None
    instruction: str | None = None


class TaskItem(BaseModel):
    """Task item schema."""

    id: str
    name: str
    target: str
    scan_mode: str
    interactive: bool
    created_by: str
    creator_name: str | None = None
    created_at: datetime
    status: str
    risk_level: str


class TaskDetail(TaskItem):
    """Task detail schema."""

    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class ExecuteRequest(BaseModel):
    """Execute task request."""

    force: bool = False


class ExecuteResponse(BaseModel):
    """Execute task response."""

    run_id: str
    status: str


class StopRequest(BaseModel):
    """Stop task request."""

    run_id: str
