"""Enum definitions."""

from enum import Enum


class UserRole(str, Enum):
    """User role."""

    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    """User status."""

    ENABLED = "enabled"
    DISABLED = "disabled"


class TaskStatus(str, Enum):
    """Task status."""

    NOT_STARTED = "not_started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class RunStatus(str, Enum):
    """Run status."""

    QUEUED = "queued"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class ScanMode(str, Enum):
    """Scan mode."""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class RiskLevel(str, Enum):
    """Risk level."""

    UNKNOWN = "unknown"
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ResultStatus(str, Enum):
    """Result status."""

    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    PARSE_FAILED = "parse_failed"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity."""

    UNKNOWN = "unknown"
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ArtifactType(str, Enum):
    """Artifact type."""

    EVENTS_JSONL = "events_jsonl"
    MARKDOWN = "markdown"
    TERMINAL_RAW = "terminal_raw"
    RUNNER_LOG = "runner_log"
    REPORT = "report"
    OTHER = "other"


class WhitelistType(str, Enum):
    """Whitelist target type."""

    URL = "url"
    DOMAIN = "domain"
    IP = "ip"
    REPO = "repo"


class WhitelistStatus(str, Enum):
    """Whitelist status."""

    ENABLED = "enabled"
    DISABLED = "disabled"


class AuditAction(str, Enum):
    """Audit action."""

    LOGIN = "login"
    LOGOUT = "logout"
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    EXECUTE_TASK = "execute_task"
    STOP_TASK = "stop_task"
    VIEW_RESULT = "view_result"
    DOWNLOAD_ARTIFACT = "download_artifact"
    CREATE_WHITELIST = "create_whitelist"
    UPDATE_WHITELIST = "update_whitelist"
    DELETE_WHITELIST = "delete_whitelist"
    ENABLE_WHITELIST = "enable_whitelist"
    DISABLE_WHITELIST = "disable_whitelist"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    ENABLE_USER = "enable_user"
    DISABLE_USER = "disable_user"
    RESET_PASSWORD = "reset_password"


class AuditResult(str, Enum):
    """Audit result."""

    SUCCESS = "success"
    FAILED = "failed"
