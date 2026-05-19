"""User service."""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.enums import UserRole, UserStatus
from app.core.errors import NotFoundException
from app.core.security import get_password_hash
from app.db.session import get_db_context
from app.models import User


class UserService:
    """User service for user management."""

    DEFAULT_PASSWORD = "123456"

    @staticmethod
    def create_user(
        db: Session,
        username: str,
        account: str,
        password: str,
        role: str,
        created_by: str,
        department: str = None,
    ) -> User:
        """Create a new user."""
        # Check if account already exists
        existing = db.query(User).filter(User.account == account).first()
        if existing:
            raise ValueError("账号已存在")

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            account=account,
            password_hash=get_password_hash(password),
            role=role,
            department=department,
            status=UserStatus.ENABLED.value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user(
        db: Session,
        user_id: str,
        username: str = None,
        role: str = None,
        department: str = None,
    ) -> User:
        """Update a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("用户不存在")

        if username is not None:
            user.username = username
        if role is not None:
            user.role = role
        if department is not None:
            user.department = department

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def toggle_user_status(db: Session, user_id: str) -> User:
        """Toggle user status."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("用户不存在")

        if user.status == UserStatus.ENABLED.value:
            user.status = UserStatus.DISABLED.value
        else:
            user.status = UserStatus.ENABLED.value

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: str) -> bool:
        """Delete a user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("用户不存在")

        db.delete(user)
        db.commit()
        return True

    @staticmethod
    def reset_password(db: Session, user_id: str) -> str:
        """Reset user password to default."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("用户不存在")

        new_password = UserService.DEFAULT_PASSWORD
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.commit()
        return new_password

    @staticmethod
    def get_users(
        db: Session,
        role: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        """Get paginated users."""
        query = db.query(User)

        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)

        total = query.count()
        offset = (page - 1) * page_size
        items = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        return items, total

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> User:
        """Get user by ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("用户不存在")
        return user
