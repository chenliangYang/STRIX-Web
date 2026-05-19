"""Authentication service."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import UserRole, UserStatus
from app.core.errors import UnauthorizedException, ForbiddenException
from app.core.security import verify_password, create_access_token
from app.db.session import get_db_context
from app.models import User, AuditLog


class AuthService:
    """Authentication service."""

    @staticmethod
    def login(db: Session, account: str, password: str, role: str = "admin") -> dict:
        """Login user and return token."""
        user = db.query(User).filter(User.account == account).first()
        
        if not user:
            raise UnauthorizedException("账号不存在")

        if not verify_password(password, user.password_hash):
            raise UnauthorizedException("密码错误")

        if user.status != UserStatus.ENABLED.value:
            raise UnauthorizedException("账号已被禁用")

        if user.role != role:
            raise ForbiddenException("角色不匹配")

        # Update last login time
        user.last_login_at = datetime.utcnow()
        db.commit()

        # Create access token
        token = create_access_token({
            "sub": user.id,
            "account": user.account,
            "role": user.role,
        })

        return {
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "account": user.account,
                "role": user.role,
            }
        }

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User | None:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_current_user(db: Session, user_id: str) -> dict:
        """Get current user info."""
        user = AuthService.get_user_by_id(db, user_id)
        if not user:
            raise UnauthorizedException("用户不存在")

        return {
            "id": user.id,
            "username": user.username,
            "account": user.account,
            "role": user.role,
            "department": user.department,
            "status": user.status,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }

    @staticmethod
    def check_permission(user_role: str, required_role: str) -> bool:
        """Check if user has permission."""
        if required_role == UserRole.ADMIN.value:
            return user_role == UserRole.ADMIN.value
        return True
