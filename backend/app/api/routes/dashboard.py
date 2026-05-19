"""Dashboard routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.schemas.common import ResponseData
from app.schemas.system import (
    DashboardSummary,
    StatusDistributionItem,
    RecentScanItem,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=ResponseData)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get dashboard summary."""
    summary = DashboardService.get_summary(db)
    return ResponseData(
        code=0,
        message="ok",
        data=summary,
    )


@router.get("/status-distribution", response_model=ResponseData)
async def get_status_distribution(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get task status distribution."""
    distribution = DashboardService.get_status_distribution(db)
    return ResponseData(
        code=0,
        message="ok",
        data=distribution,
    )


@router.get("/recent-scans", response_model=ResponseData)
async def get_recent_scans(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get recent scan records."""
    scans = DashboardService.get_recent_scans(db, limit=limit)
    return ResponseData(
        code=0,
        message="ok",
        data={
            "items": scans,
        },
    )
