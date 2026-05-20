"""Task run schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class RunItem(BaseModel):
    """Run item schema."""

    id: str
    task_id: str
    run_no: int
    scan_mode: str
    interactive: bool | int
    status: str
    pid: int | None = None
    runner_node_id: str | None = None
    exit_code: int | None = None
    run_dir: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error_message: str | None = None
    created_by: str
    created_at: datetime

    @field_validator('interactive', mode='before')
    @classmethod
    def convert_interactive(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes')
        return v

    @field_validator('run_dir', mode='before')
    @classmethod
    def convert_run_dir(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v) if v else None


class RunDetail(RunItem):
    """Run detail schema."""

    strix_run_dir: str | None = None
    updated_at: datetime | None = None


class TaskRunResponse(BaseModel):
    """TaskRun response schema."""

    id: str
    task_id: str
    run_no: int
    scan_mode: str
    interactive: bool | int
    status: str
    pid: int | None = None
    runner_node_id: str | None = None
    exit_code: int | None = None
    run_dir: str | None = None
    strix_run_dir: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error_message: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime | None = None

    @field_validator('interactive', mode='before')
    @classmethod
    def convert_interactive(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes')
        return v

    @field_validator('run_dir', mode='before')
    @classmethod
    def convert_run_dir(cls, v: Any) -> str | None:
        if v is None:
            return None
        return str(v) if v else None


class RunEventSchema(BaseModel):
    """Run event schema."""

    id: str
    run_id: str
    seq: int
    event_type: str
    event_time: datetime | None = None
    payload_json: dict
    source_file: str | None = None
    source_offset: int | None = None
    created_at: datetime


RunEventResponse = RunEventSchema


class ArtifactItem(BaseModel):
    """Artifact item schema."""

    id: str
    run_id: str
    result_id: str | None = None
    vulnerability_id: str | None = None
    artifact_type: str
    relative_path: str
    file_name: str | None = None
    content_type: str | None = None
    size_bytes: int | None = None
    sha256: str | None = None
    created_at: datetime
