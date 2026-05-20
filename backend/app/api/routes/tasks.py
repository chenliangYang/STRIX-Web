"""Task routes."""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id, require_admin
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskItem,
    TaskDetail,
    ExecuteResponse,
)
from app.services.task_service import TaskService
from app.services.run_service import RunService
from app.services.audit_service import AuditService
from app.services.whitelist_service import WhitelistService
from app.core.errors import WhitelistNotMatchedException, StrixWebException

router = APIRouter(prefix="/tasks", tags=["tasks"])


def task_to_dict(task) -> dict:
    """Convert task model to dict."""
    return {
        "id": task.id,
        "name": task.name,
        "target": task.target,
        "scan_mode": task.scan_mode,
        "interactive": task.interactive,
        "status": task.status,
        "risk_level": task.risk_level,
        "created_by": task.created_by,
        "creator_name": task.creator.username if task.creator else None,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


@router.get("", response_model=PaginatedResponse)
async def get_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str = None,
    target: str = None,
    scan_mode: str = None,
    interactive: bool = None,
    status: str = None,
    risk_level: str = None,
    created_by: str = None,
    created_at_start: str = None,
    created_at_end: str = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get task list."""
    # For non-admin users, only show their own tasks
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    is_admin = user.role == "admin"

    if not is_admin:
        created_by = user_id

    tasks, total = TaskService.get_tasks(
        db=db,
        name=name,
        target=target,
        scan_mode=scan_mode,
        interactive=interactive,
        status=status,
        risk_level=risk_level,
        created_by=created_by,
        created_at_start=created_at_start,
        created_at_end=created_at_end,
        page=page,
        page_size=page_size,
    )

    return ResponseData(
        code=0,
        message="ok",
        data=PaginatedData(
            items=[task_to_dict(t) for t in tasks],
            total=total,
            page=page,
            pageSize=page_size,
        ),
    )


@router.get("/{task_id}", response_model=ResponseData)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get task detail."""
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    is_admin = user.role == "admin"

    task = TaskService.get_task_by_id(db, task_id)

    # Check access
    if not is_admin and task.created_by != user_id:
        raise StrixWebException("没有权限访问该任务", code=40300)

    return ResponseData(
        code=0,
        message="ok",
        data=task_to_dict(task),
    )


@router.post("", response_model=ResponseData)
async def create_task(
    request: Request,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new task."""
    task = TaskService.create_task(
        db=db,
        name=task_data.name,
        target=task_data.target,
        scan_mode=task_data.scan_mode,
        created_by=user_id,
        interactive=task_data.interactive,
        instruction=task_data.instruction,
    )

    # Log audit
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    AuditService.log_task_action(
        db=db,
        action="create_task",
        task_id=task.id,
        user_id=user_id,
        account=user.account,
        role=user.role,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="任务创建成功",
        data=task_to_dict(task),
    )


@router.put("/{task_id}", response_model=ResponseData)
async def update_task(
    request: Request,
    task_id: str,
    task_data: TaskUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update a task."""
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    is_admin = user.role == "admin"

    task = TaskService.get_task_by_id(db, task_id)

    # Check access
    if not is_admin and task.created_by != user_id:
        raise StrixWebException("没有权限修改该任务", code=40300)

    updated_task = TaskService.update_task(
        db=db,
        task_id=task_id,
        name=task_data.name,
        target=task_data.target,
        scan_mode=task_data.scan_mode,
        interactive=task_data.interactive,
        instruction=task_data.instruction,
    )

    # Log audit
    AuditService.log_task_action(
        db=db,
        action="update_task",
        task_id=task_id,
        user_id=user_id,
        account=user.account,
        role=user.role,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="任务更新成功",
        data=task_to_dict(updated_task),
    )


@router.delete("/{task_id}", response_model=ResponseData)
async def delete_task(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a task (soft delete)."""
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    is_admin = user.role == "admin"

    task = TaskService.get_task_by_id(db, task_id)

    # Check access
    if not is_admin and task.created_by != user_id:
        raise StrixWebException("没有权限删除该任务", code=40300)

    TaskService.delete_task(db=db, task_id=task_id)

    # Log audit
    AuditService.log_task_action(
        db=db,
        action="delete_task",
        task_id=task_id,
        user_id=user_id,
        account=user.account,
        role=user.role,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="任务删除成功",
    )


@router.post("/{task_id}/execute", response_model=ResponseData[ExecuteResponse])
async def execute_task(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Execute a task."""
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    is_admin = user.role == "admin"

    task = TaskService.get_task_by_id(db, task_id)

    # Check access
    if not is_admin and task.created_by != user_id:
        raise StrixWebException("没有权限执行该任务", code=40300)

    # Check if target is empty
    if not task.target or not task.target.strip():
        raise StrixWebException("目标地址不能为空", code=40000)

    # Check whitelist
    allowed, matched_id = WhitelistService.check_whitelist(db, task.target)
    if not allowed:
        raise WhitelistNotMatchedException("目标不在白名单中")

    # Execute task via RunService
    run = RunService.execute_task(db, task_id, user_id)

    return ResponseData(
        code=0,
        message="任务已开始执行",
        data=ExecuteResponse(
            run_id=run.id,
            status=run.status,
        ),
    )


@router.post("/{task_id}/stop", response_model=ResponseData)
async def stop_task(
    request: Request,
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Stop a running task."""
    from app.services.auth_service import AuthService
    user = AuthService.get_user_by_id(db, user_id)
    is_admin = user.role == "admin"

    task = TaskService.get_task_by_id(db, task_id)

    # Check access
    if not is_admin and task.created_by != user_id:
        raise StrixWebException("没有权限停止该任务", code=40300)

    # Get the latest running task run
    latest_run = RunService.get_latest_run(db, task_id)
    if latest_run and latest_run.status == "running":
        RunService.stop_task(db, latest_run.id, user_id)

    # Log audit
    AuditService.log_task_action(
        db=db,
        action="stop_task",
        task_id=task_id,
        user_id=user_id,
        account=user.account,
        role=user.role,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="停止请求已发送",
    )
