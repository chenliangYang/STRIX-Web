"""Result schemas."""

from datetime import datetime

from pydantic import BaseModel


class VulnerabilityItem(BaseModel):
    """Vulnerability item schema."""

    id: str
    result_id: str
    ordinal: int
    title: str
    severity: str
    vuln_type: str | None = None
    affected_target: str | None = None
    verified: bool = False
    summary: str | None = None
    markdown_artifact_id: str | None = None
    created_at: datetime


class ResultItem(BaseModel):
    """Result item schema."""

    id: str
    task_id: str
    run_id: str
    project_name: str
    target: str
    scan_mode: str
    interactive: bool
    status: str
    risk_level: str
    vulnerability_count: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class ResultDetail(ResultItem):
    """Result detail schema."""

    artifact_dir: str | None = None
    summary: str | None = None
    parse_error: str | None = None
    updated_at: datetime | None = None


class VulnerabilityMarkdown(BaseModel):
    """Vulnerability markdown schema."""

    vuln_id: str
    title: str
    markdown: str
