"""Whitelist routes."""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id, require_admin
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.system import (
    WhitelistCreate,
    WhitelistUpdate,
    WhitelistItem,
    WhitelistCheckRequest,
    WhitelistCheckResponse,
)
from app.services.whitelist_service import WhitelistService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/whitelists", tags=["whitelists"])


def whitelist_to_dict(wl) -> dict:
    """Convert whitelist model to dict."""
    return {
        "id": wl.id,
        "name": wl.name,
        "target_type": wl.target_type,
        "target_value": wl.target_value,
        "target_normalized": wl.target_normalized,
        "project": wl.project,
        "status": wl.status,
        "created_by": wl.created_by,
        "created_at": wl.created_at.isoformat() if wl.created_at else None,
    }


@router.get("", response_model=PaginatedResponse)
async def get_whitelists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    name: str = Query(None, alias="name"),
    targetType: str = Query(None, alias="targetType"),
    status: str = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Get whitelist entries (admin only)."""
    whitelists, total = WhitelistService.get_whitelists(
        db=db,
        name=name,
        target_type=targetType,
        status=status,
        page=page,
        page_size=page_size,
    )

    return ResponseData(
        code=0,
        message="ok",
        data=PaginatedData(
            items=[whitelist_to_dict(w) for w in whitelists],
            total=total,
            page=page,
            pageSize=page_size,
        ),
    )


@router.get("/{whitelist_id}", response_model=ResponseData)
async def get_whitelist(
    whitelist_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Get whitelist detail (admin only)."""
    whitelist = WhitelistService.get_whitelist_by_id(db, whitelist_id)
    return ResponseData(
        code=0,
        message="ok",
        data=whitelist_to_dict(whitelist),
    )


@router.post("", response_model=ResponseData)
async def create_whitelist(
    request: Request,
    whitelist_data: WhitelistCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Create a new whitelist entry (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    whitelist = WhitelistService.create_whitelist(
        db=db,
        name=whitelist_data.name,
        target_type=whitelist_data.target_type,
        target_value=whitelist_data.target_value,
        created_by=user_id,
        project=whitelist_data.project,
    )

    # Log audit
    AuditService.log(
        db=db,
        action="create_whitelist",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="whitelist",
        object_id=whitelist.id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="白名单创建成功",
        data=whitelist_to_dict(whitelist),
    )


@router.put("/{whitelist_id}", response_model=ResponseData)
async def update_whitelist(
    request: Request,
    whitelist_id: str,
    whitelist_data: WhitelistUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Update a whitelist entry (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    whitelist = WhitelistService.update_whitelist(
        db=db,
        whitelist_id=whitelist_id,
        name=whitelist_data.name,
        target_type=whitelist_data.target_type,
        target_value=whitelist_data.target_value,
        project=whitelist_data.project,
    )

    if not whitelist:
        return ResponseData(code=40400, message="白名单不存在")

    # Log audit
    AuditService.log(
        db=db,
        action="update_whitelist",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="whitelist",
        object_id=whitelist_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="白名单更新成功",
        data=whitelist_to_dict(whitelist),
    )


@router.delete("/{whitelist_id}", response_model=ResponseData)
async def delete_whitelist(
    request: Request,
    whitelist_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Delete a whitelist entry (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    success = WhitelistService.delete_whitelist(db, whitelist_id)

    if not success:
        return ResponseData(code=40400, message="白名单不存在")

    # Log audit
    AuditService.log(
        db=db,
        action="delete_whitelist",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="whitelist",
        object_id=whitelist_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="白名单删除成功",
    )


@router.post("/{whitelist_id}/enable", response_model=ResponseData)
async def enable_whitelist(
    request: Request,
    whitelist_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Enable a whitelist entry (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    whitelist = WhitelistService.toggle_whitelist(db, whitelist_id)

    if not whitelist:
        return ResponseData(code=40400, message="白名单不存在")

    # Log audit
    AuditService.log(
        db=db,
        action="enable_whitelist",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="whitelist",
        object_id=whitelist_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="白名单已启用",
        data=whitelist_to_dict(whitelist),
    )


@router.post("/{whitelist_id}/disable", response_model=ResponseData)
async def disable_whitelist(
    request: Request,
    whitelist_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Disable a whitelist entry (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    whitelist = WhitelistService.toggle_whitelist(db, whitelist_id)

    if not whitelist:
        return ResponseData(code=40400, message="白名单不存在")

    # Log audit
    AuditService.log(
        db=db,
        action="disable_whitelist",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="whitelist",
        object_id=whitelist_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="白名单已禁用",
        data=whitelist_to_dict(whitelist),
    )


@router.post("/check", response_model=ResponseData[WhitelistCheckResponse])
async def check_whitelist(
    check_data: WhitelistCheckRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Check if target is in whitelist."""
    allowed, matched_id = WhitelistService.check_whitelist(db, check_data.target)

    return ResponseData(
        code=0,
        message="ok",
        data=WhitelistCheckResponse(
            allowed=allowed,
            matched_whitelist_id=matched_id,
        ),
    )
