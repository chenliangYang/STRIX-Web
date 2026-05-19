"""Task service."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enums import TaskStatus, ScanMode, RiskLevel
from app.core.errors import NotFoundException, TaskStatusNotAllowedException
from app.db.session import get_db_context
from app.models import Task, TaskRun, User
from app.services.whitelist_service import WhitelistService


class TaskService:
    """Task service for task management."""

    ALLOWED_STATUS_TRANSITIONS = {
        TaskStatus.NOT_STARTED.value: [TaskStatus.RUNNING.value],
        TaskStatus.FAILED.value: [TaskStatus.RUNNING.value],
        TaskStatus.STOPPED.value: [TaskStatus.RUNNING.value],
        TaskStatus.RUNNING.value: [
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value,
            TaskStatus.STOPPED.value,
        ],
    }

    @staticmethod
    def normalize_target(target: str) -> str:
        """Normalize target URL."""
        return WhitelistService.normalize_url(target)

    @staticmethod
    def create_task(
        db: Session,
        name: str,
        target: str,
        scan_mode: str,
        created_by: str,
        interactive: bool = False,
        instruction: str = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            target=target,
            target_normalized=TaskService.normalize_target(target),
            scan_mode=scan_mode,
            interactive=interactive,
            instruction=instruction,
            status=TaskStatus.NOT_STARTED.value,
            risk_level=RiskLevel.UNKNOWN.value,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(
        db: Session,
        task_id: str,
        name: str = None,
        target: str = None,
        scan_mode: str = None,
        interactive: bool = None,
        instruction: str = None,
    ) -> Task:
        """Update a task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundException("任务不存在")

        # Check if task is running
        if task.status == TaskStatus.RUNNING.value:
            raise TaskStatusNotAllowedException("任务正在运行中，禁止编辑")

        if name is not None:
            task.name = name
        if target is not None:
            task.target = target
            task.target_normalized = TaskService.normalize_target(target)
        if scan_mode is not None:
            task.scan_mode = scan_mode
        if interactive is not None:
            task.interactive = interactive
        if instruction is not None:
            task.instruction = instruction

        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: str) -> bool:
        """Soft delete a task."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundException("任务不存在")

        if task.status == TaskStatus.RUNNING.value:
            raise TaskStatusNotAllowedException("任务正在运行中，禁止删除")

        task.deleted_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def get_task_by_id(db: Session, task_id: str) -> Task:
        """Get task by ID."""
        task = db.query(Task).filter(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        ).first()
        if not task:
            raise NotFoundException("任务不存在")
        return task

    @staticmethod
    def get_tasks(
        db: Session,
        name: str = None,
        target: str = None,
        scan_mode: str = None,
        interactive: bool = None,
        status: str = None,
        risk_level: str = None,
        created_by: str = None,
        created_at_start: str = None,
        created_at_end: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Task], int]:
        """Get paginated tasks."""
        query = db.query(Task).filter(Task.deleted_at.is_(None))

        if name:
            query = query.filter(Task.name.like(f"%{name}%"))
        if target:
            query = query.filter(Task.target.like(f"%{target}%"))
        if scan_mode:
            query = query.filter(Task.scan_mode == scan_mode)
        if interactive is not None:
            query = query.filter(Task.interactive == interactive)
        if status:
            query = query.filter(Task.status == status)
        if risk_level:
            query = query.filter(Task.risk_level == risk_level)
        if created_by:
            query = query.filter(Task.created_by == created_by)
        if created_at_start:
            query = query.filter(Task.created_at >= created_at_start)
        if created_at_end:
            query = query.filter(Task.created_at <= created_at_end)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(Task.created_at.desc()).offset(offset).limit(page_size).all()

        return items, total

    @staticmethod
    def update_task_status(
        db: Session,
        task_id: str,
        status: str,
        risk_level: str = None,
    ) -> Task:
        """Update task status."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundException("任务不存在")

        # Validate status transition
        allowed = TaskService.ALLOWED_STATUS_TRANSITIONS.get(task.status, [])
        if status not in allowed:
            raise TaskStatusNotAllowedException(
                f"状态从 {task.status} 不能转换到 {status}"
            )

        task.status = status
        if risk_level:
            task.risk_level = risk_level
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def check_can_execute(db: Session, task_id: str) -> bool:
        """Check if task can be executed."""
        task = TaskService.get_task_by_id(db, task_id)
        if task.status == TaskStatus.RUNNING.value:
            raise TaskStatusNotAllowedException("任务正在运行中")
        return True

    @staticmethod
    def check_user_access(db: Session, task_id: str, user_id: str, is_admin: bool) -> bool:
        """Check if user has access to task."""
        if is_admin:
            return True

        task = TaskService.get_task_by_id(db, task_id)
        return task.created_by == user_id
