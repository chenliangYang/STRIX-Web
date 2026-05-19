"""Audit service."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import AuditAction, AuditResult
from app.db.session import get_db_context
from app.models import AuditLog, User
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Audit service for logging actions."""

    @staticmethod
    def log(
        db: Session,
        action: str,
        result: str = AuditResult.SUCCESS.value,
        actor_id: str = None,
        actor_account: str = None,
        actor_role: str = None,
        object_type: str = None,
        object_id: str = None,
        request_ip: str = None,
        remark: str = None,
    ):
        """Log an audit event."""
        try:
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                actor_id=actor_id,
                actor_account=actor_account,
                actor_role=actor_role,
                action=action,
                object_type=object_type,
                object_id=object_id,
                request_ip=request_ip,
                result=result,
                remark=remark,
                created_at=datetime.utcnow(),
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            db.rollback()

    @staticmethod
    def log_login(
        db: Session,
        account: str,
        role: str,
        success: bool,
        request_ip: str = None,
        remark: str = None,
    ):
        """Log login event."""
        AuditService.log(
            db=db,
            action=AuditAction.LOGIN.value,
            result=AuditResult.SUCCESS.value if success else AuditResult.FAILED.value,
            actor_account=account,
            actor_role=role,
            request_ip=request_ip,
            remark=remark,
        )

    @staticmethod
    def log_logout(
        db: Session,
        user_id: str,
        account: str,
        role: str,
        request_ip: str = None,
    ):
        """Log logout event."""
        AuditService.log(
            db=db,
            action=AuditAction.LOGOUT.value,
            actor_id=user_id,
            actor_account=account,
            actor_role=role,
            request_ip=request_ip,
        )

    @staticmethod
    def log_task_action(
        db: Session,
        action: str,
        task_id: str,
        user_id: str = None,
        account: str = None,
        role: str = None,
        request_ip: str = None,
        success: bool = True,
        remark: str = None,
    ):
        """Log task action."""
        AuditService.log(
            db=db,
            action=action,
            result=AuditResult.SUCCESS.value if success else AuditResult.FAILED.value,
            actor_id=user_id,
            actor_account=account,
            actor_role=role,
            object_type="task",
            object_id=task_id,
            request_ip=request_ip,
            remark=remark,
        )
