"""User routes."""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.schemas.common import ResponseData, PaginatedData, PaginatedResponse
from app.schemas.system import UserCreate, UserUpdate, UserItem
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/users", tags=["users"])


def user_to_dict(user, include_password: bool = False) -> dict:
    """Convert user model to dict."""
    data = {
        "id": user.id,
        "username": user.username,
        "account": user.account,
        "role": user.role,
        "department": user.department,
        "status": user.status,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }
    return data


@router.get("", response_model=PaginatedResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str = None,
    status: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Get user list (admin only)."""
    users, total = UserService.get_users(
        db=db,
        role=role,
        status=status,
        page=page,
        page_size=page_size,
    )

    return ResponseData(
        code=0,
        message="ok",
        data=PaginatedData(
            items=[user_to_dict(u) for u in users],
            total=total,
            page=page,
            pageSize=page_size,
        ),
    )


@router.get("/{target_user_id}", response_model=ResponseData)
async def get_user(
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Get user detail (admin only)."""
    user = UserService.get_user_by_id(db, target_user_id)
    return ResponseData(
        code=0,
        message="ok",
        data=user_to_dict(user),
    )


@router.post("", response_model=ResponseData)
async def create_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Create a new user (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    try:
        user = UserService.create_user(
            db=db,
            username=user_data.username,
            account=user_data.account,
            password=user_data.password,
            role=user_data.role,
            created_by=user_id,
            department=user_data.department,
        )
    except ValueError as e:
        return ResponseData(code=40900, message=str(e))

    # Log audit
    AuditService.log(
        db=db,
        action="create_user",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="user",
        object_id=user.id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="用户创建成功",
        data=user_to_dict(user),
    )


@router.put("/{target_user_id}", response_model=ResponseData)
async def update_user(
    request: Request,
    target_user_id: str,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Update a user (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    user = UserService.update_user(
        db=db,
        user_id=target_user_id,
        username=user_data.username,
        role=user_data.role,
        department=user_data.department,
    )

    # Log audit
    AuditService.log(
        db=db,
        action="update_user",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="user",
        object_id=target_user_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="用户更新成功",
        data=user_to_dict(user),
    )


@router.delete("/{target_user_id}", response_model=ResponseData)
async def delete_user(
    request: Request,
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Delete a user (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    # Prevent deleting yourself
    if target_user_id == user_id:
        return ResponseData(code=40000, message="不能删除自己")

    UserService.delete_user(db, target_user_id)

    # Log audit
    AuditService.log(
        db=db,
        action="delete_user",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="user",
        object_id=target_user_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="用户删除成功",
    )


@router.post("/{target_user_id}/enable", response_model=ResponseData)
async def enable_user(
    request: Request,
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Enable a user (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    user = UserService.toggle_user_status(db, target_user_id)

    # Log audit
    AuditService.log(
        db=db,
        action="enable_user",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="user",
        object_id=target_user_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="用户已启用",
        data=user_to_dict(user),
    )


@router.post("/{target_user_id}/disable", response_model=ResponseData)
async def disable_user(
    request: Request,
    target_user_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin),
):
    """Disable a user (admin only)."""
    user_id = current_user.get("sub")
    user_account = current_user.get("account")
    user_role = current_user.get("role")

    # Prevent disabling yourself
    if target_user_id == user_id:
        return ResponseData(code=40000, message="不能禁用自己")

    user = UserService.toggle_user_status(db, target_user_id)

    # Log audit
    AuditService.log(
        db=db,
        action="disable_user",
        actor_id=user_id,
        actor_account=user_account,
        actor_role=user_role,
        object_type="user",
        object_id=target_user_id,
        request_ip=request.client.host if request.client else None,
    )

    return ResponseData(
        code=0,
        message="用户已禁用",
        data=user_to_dict(user),
    )
