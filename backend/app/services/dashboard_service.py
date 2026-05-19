"""Dashboard service."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.enums import TaskStatus, RiskLevel
from app.db.session import get_db_context
from app.models import Task, TaskRun, Result, Vulnerability


class DashboardService:
    """Dashboard service for statistics."""

    @staticmethod
    def get_summary(db: Session) -> dict:
        """Get dashboard summary."""
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        # Active projects in last 7 days
        active_projects_7d = db.query(Task).filter(
            Task.created_at >= seven_days_ago,
            Task.deleted_at.is_(None),
        ).count()

        # Total assets scanned (completed tasks)
        total_assets_scanned = db.query(Task).filter(
            Task.status == TaskStatus.COMPLETED.value,
            Task.deleted_at.is_(None),
        ).count()

        # High risk vulnerabilities in last 30 days
        high_risk_vulns_30d = db.query(Vulnerability).join(
            Result, Vulnerability.result_id == Result.id
        ).filter(
            Result.created_at >= thirty_days_ago,
            Vulnerability.severity == RiskLevel.HIGH.value,
        ).count()

        return {
            "active_projects_7d": active_projects_7d,
            "total_assets_scanned": total_assets_scanned,
            "high_risk_vulns_30d": high_risk_vulns_30d,
        }

    @staticmethod
    def get_status_distribution(db: Session) -> list[dict]:
        """Get task status distribution."""
        status_labels = {
            TaskStatus.NOT_STARTED.value: "未开始",
            TaskStatus.RUNNING.value: "扫描中",
            TaskStatus.COMPLETED.value: "已完成",
            TaskStatus.FAILED.value: "失败",
            TaskStatus.STOPPED.value: "已停止",
        }

        distribution = []
        for status, label in status_labels.items():
            count = db.query(Task).filter(
                Task.status == status,
                Task.deleted_at.is_(None),
            ).count()
            distribution.append({
                "status": status,
                "label": label,
                "count": count,
            })

        return distribution

    @staticmethod
    def get_recent_scans(db: Session, limit: int = 10) -> list[dict]:
        """Get recent scan records."""
        from app.models import User

        tasks = db.query(Task).filter(
            Task.deleted_at.is_(None),
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
