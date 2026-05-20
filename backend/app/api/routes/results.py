"""Results API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.api.auth_deps import (
    is_admin as is_admin_check,
    assert_result_access,
    assert_vulnerability_access,
)
from app.core.errors import StrixWebException
from app.models import Result, Vulnerability, Task
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.task_run import TaskRunResponse

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=PaginatedResponse)
def get_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    taskName: str = Query(None, alias="taskName", description="Filter by task name"),
    status: str = Query(None, alias="status", description="Filter by status"),
    riskLevel: str = Query(None, alias="riskLevel", description="Filter by risk level"),
    startedAtStart: str = Query(None, alias="startedAtStart", description="Filter by start date"),
    startedAtEnd: str = Query(None, alias="startedAtEnd", description="Filter by end date"),
    createdBy: str = Query(None, alias="createdBy", description="Filter by creator"),
    sortBy: str = Query("startedAt", alias="sortBy", description="Sort field"),
    sortOrder: str = Query("desc", alias="sortOrder", description="Sort order"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get scan results list."""
    try:
        query = db.query(Result, Task).join(Task, Result.task_id == Task.id)

        # Apply user scope filter
        if not is_admin_check(current_user):
            user_id = current_user.get("sub")
            query = query.filter(Task.created_by == user_id)

        if taskName:
            query = query.filter(Task.name.like(f"%{taskName}%"))
        if status:
            query = query.filter(Result.status == status)
        if riskLevel:
            query = query.filter(Result.risk_level == riskLevel)
        if startedAtStart:
            query = query.filter(Result.started_at >= startedAtStart)
        if startedAtEnd:
            query = query.filter(Result.started_at <= startedAtEnd)
        if createdBy:
            query = query.filter(Task.created_by == createdBy)

        # Apply sorting
        sort_column = Result.started_at
        if sortBy == "createdAt":
            sort_column = Result.created_at
        elif sortBy == "riskLevel":
            sort_column = Result.risk_level

        if sortOrder == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        total = query.count()
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        items = []
        for result, task in results:
            items.append({
                "id": result.id,
                "task_id": task.id,
                "task_name": task.name,
                "target": task.target,
                "scan_mode": task.scan_mode,
                "status": result.status,
                "risk_level": result.risk_level,
                "vulnerability_count": result.vulnerability_count,
                "started_at": task.created_at.isoformat() if task.created_at else None,
                "ended_at": result.created_at.isoformat() if result.created_at else None,
            })

        return {
            "code": 0,
            "message": "ok",
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取结果列表失败: {str(e)}")


@router.get("/{result_id}", response_model=ResponseData)
def get_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get result detail."""
    try:
        # Check access permission
        result = assert_result_access(db, result_id, current_user)
        task = result.task

        return {
            "code": 0,
            "message": "ok",
            "data": {
                "id": result.id,
                "task_id": result.task_id,
                "task_name": task.name if task else None,
                "target": task.target if task else None,
                "scan_mode": task.scan_mode if task else None,
                "status": result.status,
                "risk_level": result.risk_level,
                "vulnerability_count": result.vulnerability_count,
                "created_at": result.created_at.isoformat() if result.created_at else None,
            },
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取结果详情失败: {str(e)}")


@router.get("/{result_id}/vulnerabilities", response_model=ResponseData)
def get_result_vulnerabilities(
    result_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get vulnerabilities for a result."""
    try:
        # Check access permission to the result
        assert_result_access(db, result_id, current_user)

        query = db.query(Vulnerability).filter(Vulnerability.result_id == result_id)
        total = query.count()
        offset = (page - 1) * page_size
        vulns = query.order_by(
            Vulnerability.severity.desc(),
            Vulnerability.created_at.desc()
        ).offset(offset).limit(page_size).all()

        items = []
        for v in vulns:
            items.append({
                "id": v.id,
                "vuln_id": v.vuln_id,
                "title": v.title,
                "severity": v.severity,
                "vuln_type": v.vuln_type,
                "affected_target": v.affected_target,
                "verified": v.verified,
                "summary": v.summary,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            })

        return {
            "code": 0,
            "message": "ok",
            "data": {
                "items": items,
                "total": total,
                "page": page,
                "pageSize": page_size,
            },
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取漏洞列表失败: {str(e)}")


@router.get("/vulnerabilities/{vuln_id}/markdown", response_model=ResponseData)
def get_vulnerability_markdown(
    vuln_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get vulnerability markdown content."""
    try:
        # Check access permission
        vuln = assert_vulnerability_access(db, vuln_id, current_user)

        # Read markdown content from raw_json if markdown_path is not set
        if not vuln.raw_json or not vuln.raw_json.get("content_preview"):
            raise StrixWebException("漏洞报告内容不存在", code=40400)

        # Get content from raw_json
        content = vuln.raw_json.get("content_preview", "")

        return {
            "code": 0,
            "message": "ok",
            "data": {
                "content": content,
                "vuln_id": vuln.vuln_id,
                "title": vuln.title,
                "severity": vuln.severity,
            },
        }
    except StrixWebException as e:
        raise e
    except Exception as e:
        raise StrixWebException(code=50000, message=f"获取漏洞报告失败: {str(e)}")
