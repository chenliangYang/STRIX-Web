"""Results API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.errors import StrixWebException
from app.models import User, Result, Vulnerability, Task
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.task_run import TaskRunResponse

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=PaginatedResponse)
def get_results(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    taskName: str = Query(None, description="Filter by task name"),
    status: str = Query(None, description="Filter by status"),
    riskLevel: str = Query(None, description="Filter by risk level"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get scan results list."""
    try:
        query = db.query(Result, Task).join(Task, Result.task_id == Task.id)

        if taskName:
            query = query.filter(Task.name.like(f"%{taskName}%"))
        if status:
            query = query.filter(Result.status == status)
        if riskLevel:
            query = query.filter(Result.risk_level == riskLevel)

        total = query.count()
        offset = (page - 1) * page_size
        results = query.order_by(Result.created_at.desc()).offset(offset).limit(page_size).all()

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
    current_user: User = Depends(get_current_user),
):
    """Get result detail."""
    try:
        result = db.query(Result).filter(Result.id == result_id).first()
        if not result:
            raise StrixWebException("结果不存在", code=40400)

        task = db.query(Task).filter(Task.id == result.task_id).first()

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
    current_user: User = Depends(get_current_user),
):
    """Get vulnerabilities for a result."""
    try:
        result = db.query(Result).filter(Result.id == result_id).first()
        if not result:
            raise StrixWebException("结果不存在", code=40400)

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
    current_user: User = Depends(get_current_user),
):
    """Get vulnerability markdown content."""
    try:
        vuln = db.query(Vulnerability).filter(Vulnerability.id == vuln_id).first()
        if not vuln:
            raise StrixWebException("漏洞不存在", code=40400)

        if not vuln.markdown_path:
            raise StrixWebException("漏洞报告文件不存在", code=40400)

        # Security: validate path is within allowed directory
        from pathlib import Path
        from app.core.config import get_settings
        settings = get_settings()

        base_dir = Path(settings.runs_dir)
        file_path = base_dir / vuln.markdown_path

        # Ensure the file is within the base directory
        try:
            file_path = file_path.resolve()
            base_dir = base_dir.resolve()
            if not str(file_path).startswith(str(base_dir)):
                raise StrixWebException("无效的文件路径", code=40300)
        except Exception:
            raise StrixWebException("无效的文件路径", code=40300)

        if not file_path.exists():
            raise StrixWebException("文件不存在", code=40400)

        content = file_path.read_text(encoding="utf-8")

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
