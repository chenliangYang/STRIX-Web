"""WebSocket schemas."""

from datetime import datetime

from pydantic import BaseModel


class WSMessage(BaseModel):
    """WebSocket message."""

    type: str
    run_id: str | None = None


class WSEvent(WSMessage):
    """WebSocket event message."""

    seq: int = 0
    event_type: str = ""
    payload: dict = {}
    timestamp: datetime | None = None


class WSStatus(WSMessage):
    """WebSocket status message."""

    task_id: str | None = None
    run_status: str | None = None
    task_status: str | None = None
    timestamp: datetime | None = None


class WSError(WSMessage):
    """WebSocket error message."""

    message: str = ""


class WSTerminalInput(BaseModel):
    """WebSocket terminal input."""

    type: str = "input"
    data: str = ""


class WSTerminalResize(BaseModel):
    """WebSocket terminal resize."""

    type: str = "resize"
    cols: int = 120
    rows: int = 36


class WSTerminalPing(BaseModel):
    """WebSocket terminal ping."""

    type: str = "ping"
