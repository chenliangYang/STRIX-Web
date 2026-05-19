"""Audit log routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.system import AuditLogItem
from app.services.auth_service import AuthService
from app.models import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def audit_log_to_dict(log) -> dict:
    """Convert audit log model to dict."""
    return {
        "id": log.id,
        "actor_id": log.actor_id,
        "actor_account": log.actor_account,
        "actor_role": log.actor_role,
        "action": log.action,
        "object_type": log.object_type,
        "object_id": log.object_id,
        "request_ip": log.request_ip,
        "result": log.result,
        "remark": log.remark,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("", response_model=PaginatedResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor: str = None,
    action: str = None,
    result: str = None,
    created_at_start: str = None,
    created_at_end: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_admin),
):
    """Get audit logs (admin only)."""
    query = db.query(AuditLog)

    if actor:
        query = query.filter(AuditLog.actor_account.like(f"%{actor}%"))
    if action:
        query = query.filter(AuditLog.action == action)
    if result:
        query = query.filter(AuditLog.result == result)
    if created_at_start:
        query = query.filter(AuditLog.created_at >= created_at_start)
    if created_at_end:
        query = query.filter(AuditLog.created_at <= created_at_end)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    return ResponseData(
        code=0,
        message="ok",
        data=PaginatedData(
            items=[audit_log_to_dict(l) for l in logs],
            total=total,
            page=page,
            pageSize=page_size,
        ),
    )
