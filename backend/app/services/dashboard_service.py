"""Dashboard service."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.core.enums import TaskStatus, RiskLevel
from app.db.session import get_db_context
from app.models import Task, TaskRun, Result, Vulnerability, User


class DashboardService:
    """Dashboard service for statistics."""

    @staticmethod
    def _get_task_filter(current_user: dict):
        """Get task filter based on user role."""
        base_filter = [Task.deleted_at.is_(None)]

        if not is_admin_static(current_user):
            user_id = current_user.get("sub")
            base_filter.append(Task.created_by == user_id)

        return base_filter

    @staticmethod
    def get_summary(db: Session, current_user: dict) -> dict:
        """Get dashboard summary."""
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        task_filter = DashboardService._get_task_filter(current_user)

        # Active projects in last 7 days
        active_projects_7d = db.query(Task).filter(
            *task_filter,
            Task.created_at >= seven_days_ago,
        ).count()

        # Total assets scanned (completed tasks)
        total_assets_scanned = db.query(Task).filter(
            *task_filter,
            Task.status == TaskStatus.COMPLETED.value,
        ).count()

        # High risk vulnerabilities in last 30 days
        if is_admin_static(current_user):
            # Admin sees all high risk vulns
            high_risk_vulns_30d = db.query(Vulnerability).join(
                Result, Vulnerability.result_id == Result.id
            ).filter(
                Result.created_at >= thirty_days_ago,
                Vulnerability.severity == RiskLevel.HIGH.value,
            ).count()
        else:
            # Regular user only sees their own high risk vulns
            user_id = current_user.get("sub")
            high_risk_vulns_30d = db.query(Vulnerability).join(
                Result, Vulnerability.result_id == Result.id
            ).join(
                Task, Result.task_id == Task.id
            ).filter(
                Task.created_by == user_id,
                Result.created_at >= thirty_days_ago,
                Vulnerability.severity == RiskLevel.HIGH.value,
            ).count()

        return {
            "active_projects_7d": active_projects_7d,
            "total_assets_scanned": total_assets_scanned,
            "high_risk_vulns_30d": high_risk_vulns_30d,
        }

    @staticmethod
    def get_status_distribution(db: Session, current_user: dict) -> list[dict]:
        """Get task status distribution."""
        status_labels = {
            TaskStatus.NOT_STARTED.value: "未开始",
            TaskStatus.RUNNING.value: "扫描中",
            TaskStatus.COMPLETED.value: "已完成",
            TaskStatus.FAILED.value: "失败",
            TaskStatus.STOPPED.value: "已停止",
        }

        task_filter = DashboardService._get_task_filter(current_user)

        distribution = []
        for status, label in status_labels.items():
            count = db.query(Task).filter(
                *task_filter,
                Task.status == status,
            ).count()
            distribution.append({
                "status": status,
                "label": label,
                "count": count,
            })

        return distribution

    @staticmethod
    def get_recent_scans(db: Session, current_user: dict, limit: int = 10) -> list[dict]:
        """Get recent scan records."""
        task_filter = DashboardService._get_task_filter(current_user)

        tasks = db.query(Task).filter(
            *task_filter,
        ).order_by(Task.created_at.desc()).limit(limit).all()

        results = []
        for task in tasks:
            user = db.query(User).filter(User.id == task.created_by).first()
            results.append({
                "task_id": task.id,
                "task_name": task.name,
                "target": task.target,
                "creator": user.username if user else "未知",
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "scan_status": task.status,
                "risk_level": task.risk_level,
            })

        return results


def is_admin_static(user: dict) -> bool:
    """Check if user is admin (static version for service layer)."""
    return user.get("role") == "admin"
