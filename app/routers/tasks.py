"""
Task management router.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.schemas import Task, TaskStatusUpdate, TokenData
from app.routers.deps import get_current_user
from app.services import task_service

router = APIRouter()


@router.get("/", response_model=List[Task])
def list_my_tasks(current_user: TokenData = Depends(get_current_user)):
    """List all tasks assigned to the authenticated worker, ordered by priority."""
    return task_service.list_tasks_for_user(current_user.user_id)


@router.get("/next", response_model=Task)
def get_next_task(current_user: TokenData = Depends(get_current_user)):
    """Return the highest-priority pending task for the authenticated worker."""
    task = task_service.get_next_task(current_user.user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending tasks found",
        )
    return task


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get a specific task by ID."""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}/status", response_model=Task)
def update_task_status(
    task_id: str,
    update: TaskStatusUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Update the status of a task (supports voice-initiated updates)."""
    updated = task_service.update_task_status(task_id, update, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated
