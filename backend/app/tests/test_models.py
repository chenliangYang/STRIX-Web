"""Test models."""

import uuid
from datetime import datetime

from app.core.security import get_password_hash, verify_password
from app.db.session import get_db_context


def test_user_model():
    """Test User model."""
    from app.models import User

    with get_db_context() as db:
        # Query existing users
        users = db.query(User).all()
        assert len(users) >= 2, "Should have at least admin and test user"

        # Find admin user
        admin = db.query(User).filter(User.account == "admin").first()
        assert admin is not None, "Admin user should exist"
        assert admin.role == "admin"
        assert admin.username == "管理员"
        print(f"  Admin user: {admin.username} ({admin.account})")

        # Verify password
        assert verify_password("123456", admin.password_hash), "Password should match"
        print("  Password verification: OK")

        # Find test user
        test_user = db.query(User).filter(User.account == "user").first()
        assert test_user is not None, "Test user should exist"
        assert test_user.role == "user"
        print(f"  Test user: {test_user.username} ({test_user.account})")


def test_whitelist_model():
    """Test Whitelist model."""
    from app.models import Whitelist

    with get_db_context() as db:
        whitelists = db.query(Whitelist).all()
        assert len(whitelists) >= 2, "Should have at least 2 whitelist entries"

        for wl in whitelists:
            print(f"  Whitelist: {wl.name} ({wl.target_type}: {wl.target_value})")
            assert wl.status == "enabled"


def test_task_model():
    """Test Task model."""
    from app.models import Task, User

    with get_db_context() as db:
        # Create a test task
        admin = db.query(User).filter(User.account == "admin").first()
        
        task = Task(
            id=str(uuid.uuid4()),
            name="Test Task",
            target="https://example.com",
            target_normalized="example.com",
            scan_mode="standard",
            interactive=False,
            status="not_started",
            risk_level="unknown",
            created_by=admin.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()

        # Query task
        saved_task = db.query(Task).filter(Task.id == task.id).first()
        assert saved_task is not None
        assert saved_task.name == "Test Task"
        assert saved_task.status == "not_started"
        print(f"  Task created and retrieved: {saved_task.name}")

        # Clean up
        db.delete(saved_task)
        db.commit()
        print("  Task deleted")


def test_password_hashing():
    """Test password hashing."""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password, "Hashed password should differ from original"
    assert verify_password(password, hashed), "Password verification should pass"
    assert not verify_password("wrong_password", hashed), "Wrong password should fail"
    print("  Password hashing: OK")


def test_enums():
    """Test enum values."""
    from app.core.enums import UserRole, TaskStatus, ScanMode

    # These are just Python enums for type hints
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.USER.value == "user"
    assert TaskStatus.NOT_STARTED.value == "not_started"
    assert ScanMode.STANDARD.value == "standard"
    print("  Enums: OK")


def run_tests():
    """Run all tests."""
    print("\n=== Running Model Tests ===\n")
    
    print("1. Testing User model...")
    test_user_model()
    
    print("\n2. Testing Whitelist model...")
    test_whitelist_model()
    
    print("\n3. Testing Task model...")
    test_task_model()
    
    print("\n4. Testing password hashing...")
    test_password_hashing()
    
    print("\n5. Testing enums...")
    test_enums()
    
    print("\n=== All Tests Passed ===\n")


if __name__ == "__main__":
    run_tests()
