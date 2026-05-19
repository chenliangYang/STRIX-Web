"""Database seed script."""

import uuid
from datetime import datetime

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.session import get_db_context

settings = get_settings()


def seed_admin_user(db):
    """Create admin user if not exists."""
    from app.models import User
    from app.core.enums import UserRole, UserStatus

    existing = db.query(User).filter(User.account == "admin").first()
    if existing:
        print("Admin user already exists")
        return existing

    admin = User(
        id=str(uuid.uuid4()),
        username="管理员",
        account="admin",
        password_hash=get_password_hash("123456"),
        role=UserRole.ADMIN.value,
        department="IT",
        status=UserStatus.ENABLED.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(admin)
    db.commit()
    print("Admin user created: admin / 123456")
    return admin


def seed_test_user(db):
    """Create test user if not exists."""
    from app.models import User
    from app.core.enums import UserRole, UserStatus

    existing = db.query(User).filter(User.account == "user").first()
    if existing:
        print("Test user already exists")
        return existing

    user = User(
        id=str(uuid.uuid4()),
        username="测试用户",
        account="user",
        password_hash=get_password_hash("123456"),
        role=UserRole.USER.value,
        department="Security",
        status=UserStatus.ENABLED.value,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    print("Test user created: user / 123456")
    return user


def seed_sample_whitelist(db):
    """Create sample whitelist entries."""
    from app.models import Whitelist, User
    from app.core.enums import WhitelistType, WhitelistStatus

    existing = db.query(Whitelist).first()
    if existing:
        print("Whitelist entries already exist")
        return

    admin_user = db.query(User).filter(User.account == "admin").first()
    admin_id = admin_user.id if admin_user else None
    
    if not admin_id:
        print("Admin user not found, skipping whitelist creation")
        return

    whitelists = [
        Whitelist(
            id=str(uuid.uuid4()),
            name="示例域名白名单",
            target_type=WhitelistType.DOMAIN.value,
            target_value="example.com",
            target_normalized="example.com",
            project="测试项目",
            status=WhitelistStatus.ENABLED.value,
            created_by=admin_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
        Whitelist(
            id=str(uuid.uuid4()),
            name="测试URL白名单",
            target_type=WhitelistType.URL.value,
            target_value="https://test.example.com",
            target_normalized="https://test.example.com",
            project="测试项目",
            status=WhitelistStatus.ENABLED.value,
            created_by=admin_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ),
    ]

    for whitelist in whitelists:
        db.add(whitelist)

    db.commit()
    print(f"Created {len(whitelists)} whitelist entries")


def main():
    """Run seed script."""
    print("Starting database seed...")
    print(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'localhost'}")

    with get_db_context() as db:
        admin = seed_admin_user(db)
        seed_test_user(db)
        seed_sample_whitelist(db)

    print("Database seed completed!")


if __name__ == "__main__":
    main()
