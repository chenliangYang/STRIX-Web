"""Task run schemas."""

from datetime import datetime

from pydantic import BaseModel


class RunItem(BaseModel):
    """Run item schema."""

    id: str
    task_id: str
    run_no: int
    scan_mode: str
    interactive: bool
    status: str
    pid: int | None = None
    runner_node_id: str | None = None
    exit_code: int | None = None
    run_dir: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    error_message: str | None = None
    created_by: str
    created_at: datetime


class RunDetail(RunItem):
    """Run detail schema."""

    strix_run_dir: str | None = None
    updated_at: datetime | None = None


class RunEvent(BaseModel):
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
