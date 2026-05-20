"""Authentication and authorization utilities."""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.enums import UserRole
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Task, TaskRun, Result, Vulnerability


def is_admin(user: dict) -> bool:
    """Check if user is admin."""
    return user.get("role") == UserRole.ADMIN.value


def is_owner(user: dict, created_by: str) -> bool:
    """Check if user is the owner of the resource."""
    return user.get("sub") == created_by


def apply_user_scope(db: Session, query, model, current_user: dict):
    """
    Apply user scope filter to query.
    Admin can see all data, regular users can only see their own data.
    """
    if is_admin(current_user):
        return query

    user_id = current_user.get("sub")
    if user_id is None:
        return query.filter(model.id == "never_match")

    # Apply scope based on model type
    model_name = model.__name__
    if model_name == "Task":
        return query.filter(model.created_by == user_id)
    elif model_name == "TaskRun":
        return query.filter(model.created_by == user_id)
    elif model_name == "Result":
        # Result -> Task -> created_by
        return query.join(Task).filter(Task.created_by == user_id)
    elif model_name == "Vulnerability":
        # Vulnerability -> Result -> Task -> created_by
        return query.join(Result).join(Task).filter(Task.created_by == user_id)
    else:
        return query.filter(model.created_by == user_id)


def assert_task_access(db: Session, task_id: str, current_user: dict) -> Task:
    """
    Assert user has access to the task.
    Admin can access any task, regular users can only access their own tasks.
    Returns the task if access is allowed.
    Raises 404 if task not found or user doesn't have access.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Admin can access any task
    if is_admin(current_user):
        return task

    # Regular users can only access their own tasks
    if task.created_by != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


def assert_task_access_403(db: Session, task_id: str, current_user: dict) -> Task:
    """
    Assert user has access to the task.
    Admin can access any task, regular users can only access their own tasks.
    Returns the task if access is allowed.
    Raises 403 if user doesn't have access, 404 if task not found.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Admin can access any task
    if is_admin(current_user):
        return task

    # Regular users can only access their own tasks
    if task.created_by != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this task"
        )

    return task


def assert_run_access(db: Session, run_id: str, current_user: dict) -> TaskRun:
    """
    Assert user has access to the run.
    Admin can access any run, regular users can only access runs of their own tasks.
    Returns the run if access is allowed.
    Raises 404 if run not found or user doesn't have access.
    """
    run = db.query(TaskRun).filter(TaskRun.id == run_id).first()

    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    # Admin can access any run
    if is_admin(current_user):
        return run

    # Regular users can only access runs of their own tasks
    if run.created_by != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )

    return run


def assert_result_access(db: Session, result_id: str, current_user: dict) -> Result:
    """
    Assert user has access to the result.
    Admin can access any result, regular users can only access results of their own tasks.
    Returns the result if access is allowed.
    Raises 404 if result not found or user doesn't have access.
    """
    result = db.query(Result).options(
        joinedload(Result.task)
    ).filter(Result.id == result_id).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    # Admin can access any result
    if is_admin(current_user):
        return result

    # Regular users can only access results of their own tasks
    if result.task.created_by != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )

    return result


def assert_vulnerability_access(db: Session, vuln_id: str, current_user: dict) -> Vulnerability:
    """
    Assert user has access to the vulnerability.
    Admin can access any vulnerability, regular users can only access vulnerabilities of their own results.
    Returns the vulnerability if access is allowed.
    Raises 404 if vulnerability not found or user doesn't have access.
    """
    vuln = db.query(Vulnerability).options(
        joinedload(Vulnerability.result).joinedload(Result.task)
    ).filter(Vulnerability.id == vuln_id).first()

    if vuln is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    # Admin can access any vulnerability
    if is_admin(current_user):
        return vuln

    # Regular users can only access vulnerabilities of their own results
    if vuln.result.task.created_by != current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found"
        )

    return vuln


def get_user_task_runs(db: Session, task_id: str, current_user: dict, query=None):
    """
    Get runs for a specific task with user scope.
    Admin can see all runs, regular users can only see runs of their own tasks.
    """
    # First verify task access
    assert_task_access(db, task_id, current_user)

    if query is None:
        query = db.query(TaskRun)

    return query.filter(TaskRun.task_id == task_id)


def filter_results_by_user(db: Session, query, current_user: dict):
    """
    Filter results query by user scope.
    Admin can see all results, regular users can only see results of their own tasks.
    """
    if is_admin(current_user):
        return query

    user_id = current_user.get("sub")
    if user_id is None:
        return query.filter(Result.id == "never_match")

    return query.join(Task).filter(Task.created_by == user_id)


def filter_vulnerabilities_by_user(db: Session, query, current_user: dict):
    """
    Filter vulnerabilities query by user scope.
    Admin can see all vulnerabilities, regular users can only see vulnerabilities of their own results.
    """
    if is_admin(current_user):
        return query

    user_id = current_user.get("sub")
    if user_id is None:
        return query.filter(Vulnerability.id == "never_match")

    return query.join(Result).join(Task).filter(Task.created_by == user_id)
