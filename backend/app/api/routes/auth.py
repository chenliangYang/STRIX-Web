"""Auth routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_id
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.schemas.common import ResponseData
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ResponseData[LoginResponse])
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login endpoint."""
    success = False
    error_msg = None
    
    try:
        result = AuthService.login(
            db=db,
            account=login_data.account,
            password=login_data.password,
            role=login_data.role,
        )
        success = True
        
        # Log successful login
        AuditService.log_login(
            db=db,
            account=login_data.account,
            role=login_data.role,
            success=True,
            request_ip=request.client.host if request.client else None,
        )
        
        return ResponseData(
            code=0,
            message="登录成功",
            data=LoginResponse(
                token=result["token"],
                user=UserInfo(**result["user"]),
            ),
        )
    except Exception as e:
        error_msg = str(e)
        # Log failed login
        AuditService.log_login(
            db=db,
            account=login_data.account,
            role=login_data.role,
            success=False,
            request_ip=request.client.host if request.client else None,
            remark=error_msg,
        )
        raise


@router.get("/me", response_model=ResponseData[UserInfo])
async def get_me(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current user info."""
    user_info = AuthService.get_current_user(db=db, user_id=user_id)
    return ResponseData(
        code=0,
        message="ok",
        data=UserInfo(**user_info),
    )


@router.post("/logout", response_model=ResponseData)
async def logout(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Logout endpoint."""
    user = AuthService.get_user_by_id(db=db, user_id=user_id)
    
    AuditService.log_logout(
        db=db,
        user_id=user_id,
        account=user.account if user else None,
        role=user.role if user else None,
        request_ip=request.client.host if request.client else None,
    )
    
    return ResponseData(code=0, message="ok")
