"""WebSocket handlers for real-time events."""

import asyncio
import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infra.event_bus import get_event_bus, EventBus
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

settings = get_settings()

router = APIRouter(tags=["websockets"])


def verify_ws_token(token: str) -> Optional[dict]:
    """Verify JWT token for WebSocket connection."""
    try:
        payload = decode_access_token(token)
        return payload
    except Exception as e:
        logger.warning(f"WebSocket token verification failed: {e}")
        return None


def check_run_access(run_id: str, user: dict, db: Session) -> bool:
    """
    Check if user has access to the run.
    Admin can access any run, regular users can only access runs of their own tasks.
    """
    from app.models import TaskRun, Task
    from app.core.enums import UserRole

    is_admin = user.get("role") == UserRole.ADMIN.value
    if is_admin:
        return True

    run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
    if not run:
        return False

    return run.created_by == user.get("sub")


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, run_id: str) -> None:
        """Connect a new WebSocket."""
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        self.active_connections[run_id].append(websocket)
        logger.info(f"WebSocket connected: run_id={run_id}, total={len(self.active_connections[run_id])}")

    def disconnect(self, websocket: WebSocket, run_id: str) -> None:
        """Disconnect a WebSocket."""
        if run_id in self.active_connections:
            if websocket in self.active_connections[run_id]:
                self.active_connections[run_id].remove(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]
        logger.info(f"WebSocket disconnected: run_id={run_id}")

    async def broadcast(self, run_id: str, message: dict) -> None:
        """Broadcast message to all connections for a run."""
        if run_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[run_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    disconnected.append(connection)

            for conn in disconnected:
                self.disconnect(conn, run_id)


manager = ConnectionManager()


@router.websocket("/ws/runs/{run_id}/events")
async def websocket_run_events(
    websocket: WebSocket,
    run_id: str,
    token: Optional[str] = Query(None),
):
    """WebSocket endpoint for receiving run events.

    Connect: ws://host/ws/runs/{run_id}/events?token={jwt_token}
    """
    # Token verification is mandatory
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return

    try:
        from app.services.auth_service import AuthService
        from app.db.session import get_db as _get_db

        user = AuthService.verify_token(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        # Verify run access permission
        db_gen = _get_db()
        db = next(db_gen)
        try:
            if not check_run_access(run_id, user, db):
                await websocket.close(code=4003, reason="Access denied")
                return
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await manager.connect(websocket, run_id)

    try:
        event_bus = get_event_bus()
        pubsub = event_bus.subscribe_to_run(run_id)

        if pubsub:
            asyncio.create_task(_listen_to_pubsub(websocket, pubsub, run_id))

        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, run_id)


async def _listen_to_pubsub(websocket: WebSocket, pubsub, run_id: str) -> None:
    """Listen to Redis pubsub and forward messages to WebSocket."""
    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except json.JSONDecodeError:
                    pass
    except Exception as e:
        logger.warning(f"Pubsub listener error: {e}")


@router.websocket("/ws/runs/{run_id}/terminal")
async def websocket_terminal(
    websocket: WebSocket,
    run_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for terminal (interactive mode).

    This is a placeholder for future interactive terminal support.
    """
    try:
        from app.services.auth_service import AuthService
        from app.db.session import get_db as _get_db

        user = AuthService.verify_token(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        # Verify run access permission
        db_gen = _get_db()
        db = next(db_gen)
        try:
            if not check_run_access(run_id, user, db):
                await websocket.close(code=4003, reason="Access denied")
                return
        finally:
            db.close()
    except Exception as e:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "terminal_output",
                "data": f"Terminal mode for run {run_id} not implemented yet",
            })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Terminal WebSocket error: {e}")
