"""Run service for managing task executions."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enums import TaskStatus
from app.core.errors import NotFoundException, TaskStatusNotAllowedException, WhitelistNotMatchedException
from app.db.session import get_db_context
from app.models import Task, TaskRun, RunEvent
from app.services.audit_service import AuditService
from app.services.task_service import TaskService
from app.services.whitelist_service import WhitelistService
from app.strix.runner import get_strix_runner

logger = logging.getLogger(__name__)


class RunService:
    """Service for managing task runs."""

    @staticmethod
    def execute_task(db: Session, task_id: str, user_id: str) -> TaskRun:
        """Execute a task.

        Args:
            db: Database session
            task_id: Task ID to execute
            user_id: User ID executing the task

        Returns:
            TaskRun: The created run record

        Raises:
            NotFoundException: If task not found
            TaskStatusNotAllowedException: If task is running
            WhitelistNotMatchedException: If target not in whitelist
        """
        task = TaskService.get_task_by_id(db, task_id)

        if not TaskService.check_user_access(db, task_id, user_id, False):
            raise NotFoundException("任务不存在或无权限访问")

        if task.status == TaskStatus.RUNNING.value:
            raise TaskStatusNotAllowedException("任务正在运行中")

        # Note: Whitelist check is done in the route before calling this method

        AuditService.log(
            db=db,
            action="task.execute",
            actor_id=user_id,
            object_type="task",
            object_id=task_id,
        )

        runner = get_strix_runner()
        return runner.run(db, task_id, user_id)

    @staticmethod
    def stop_task(db: Session, run_id: str, user_id: str) -> bool:
        """Stop a running task.

        Args:
            db: Database session
            run_id: Run ID to stop
            user_id: User ID stopping the task

        Returns:
            bool: True if stopped successfully
        """
        run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
        if not run:
            raise NotFoundException("运行记录不存在")

        if not TaskService.check_user_access(db, run.task_id, user_id, False):
            raise NotFoundException("无权限停止此任务")

        AuditService.log(
            db=db,
            action="task.stop",
            actor_id=user_id,
            object_type="task_run",
            object_id=run_id,
        )

        runner = get_strix_runner()
        return runner.stop(db, run_id, user_id)

    @staticmethod
    def get_run_by_id(db: Session, run_id: str) -> TaskRun:
        """Get a run by ID.

        Args:
            db: Database session
            run_id: Run ID

        Returns:
            TaskRun: The run record
        """
        run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
        if not run:
            raise NotFoundException("运行记录不存在")
        return run

    @staticmethod
    def get_runs_by_task(
        db: Session,
        task_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TaskRun], int]:
        """Get runs for a task.

        Args:
            db: Database session
            task_id: Task ID
            page: Page number
            page_size: Page size

        Returns:
            tuple: (runs list, total count)
        """
        query = db.query(TaskRun).filter(TaskRun.task_id == task_id)

        total = query.count()
        offset = (page - 1) * page_size
        runs = query.order_by(TaskRun.created_at.desc()).offset(offset).limit(page_size).all()

        return runs, total

    @staticmethod
    def get_run_events(
        db: Session,
        run_id: str,
        seq_after: int = 0,
        limit: int = 100,
    ) -> list[RunEvent]:
        """Get events for a run.

        Args:
            db: Database session
            run_id: Run ID
            seq_after: Only return events with seq > seq_after
            limit: Maximum number of events to return

        Returns:
            list[RunEvent]: List of events
        """
        run = db.query(TaskRun).filter(TaskRun.id == run_id).first()
        if not run:
            raise NotFoundException("运行记录不存在")

        query = db.query(RunEvent).filter(
            RunEvent.run_id == run_id,
            RunEvent.seq > seq_after,
        ).order_by(RunEvent.seq)

        if limit > 0:
            query = query.limit(limit)

        return query.all()

    @staticmethod
    def get_latest_run(db: Session, task_id: str) -> Optional[TaskRun]:
        """Get the latest run for a task.

        Args:
            db: Database session
            task_id: Task ID

        Returns:
            TaskRun or None
        """
        return db.query(TaskRun).filter(
            TaskRun.task_id == task_id
        ).order_by(TaskRun.created_at.desc()).first()
