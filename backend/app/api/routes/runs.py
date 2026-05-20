"""Run API routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.errors import StrixWebException
from app.models import User
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.task_run import TaskRunResponse, RunEventResponse
from app.services.run_service import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/{run_id}/stop", response_model=dict)
def stop_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop a running task."""
    try:
        success = RunService.stop_task(db, run_id, current_user.id)
        return {
            "code": 0,
            "message": "ok" if success else "failed",
            "data": {"stopped": success},
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"停止任务失败: {str(e)}")


@router.get("/{run_id}", response_model=dict)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a run by ID."""
    try:
        run = RunService.get_run_by_id(db, run_id)
        run_dict = {
            "id": run.id,
            "task_id": run.task_id,
            "run_no": run.run_no,
            "scan_mode": run.scan_mode,
            "interactive": bool(run.interactive) if run.interactive is not None else False,
            "status": run.status,
            "pid": run.pid,
            "runner_node_id": run.runner_node_id,
            "exit_code": run.exit_code,
            "run_dir": run.run_dir,
            "strix_run_dir": run.strix_run_dir,
            "started_at": run.started_at,
            "ended_at": run.ended_at,
            "error_message": run.error_message,
            "created_by": run.created_by,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
        }
        return {
            "code": 0,
            "message": "ok",
            "data": TaskRunResponse.model_validate(run_dict).model_dump(),
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取运行记录失败: {str(e)}")


@router.get("/{run_id}/events", response_model=dict)
def get_run_events(
    run_id: str,
    seq_after: int = Query(0, description="Only return events with seq > seq_after"),
    limit: int = Query(100, ge=1, le=1000, description="Max events to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get events for a run."""
    try:
        events = RunService.get_run_events(db, run_id, seq_after, limit)
        return {
            "code": 0,
            "message": "ok",
            "data": [RunEventResponse.model_validate(e).model_dump() for e in events],
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取运行事件失败: {str(e)}")


# Task runs endpoint - nested under tasks prefix
task_runs_router = APIRouter(prefix="/tasks", tags=["task_runs"])


@task_runs_router.get("/{task_id}/runs", response_model=PaginatedResponse)
def get_task_runs(
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get runs for a task."""
    try:
        runs, total = RunService.get_runs_by_task(db, task_id, page, page_size)
        
        # Convert ORM objects to dicts
        run_items = []
        for r in runs:
            run_dict = {
                "id": r.id,
                "task_id": r.task_id,
                "run_no": r.run_no,
                "scan_mode": r.scan_mode,
                "interactive": bool(r.interactive) if r.interactive is not None else False,
                "status": r.status,
                "pid": r.pid,
                "runner_node_id": r.runner_node_id,
                "exit_code": r.exit_code,
                "run_dir": r.run_dir,
                "strix_run_dir": r.strix_run_dir,
                "started_at": r.started_at,
                "ended_at": r.ended_at,
                "error_message": r.error_message,
                "created_by": r.created_by,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            run_items.append(TaskRunResponse.model_validate(run_dict))
        
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "items": [r.model_dump() for r in run_items],
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取运行记录失败: {str(e)}")
