"""
Task / workflow management service.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.schemas import AuditLog, Task, TaskStatus, TaskStatusUpdate, TaskType
from app.models.store import AUDIT_LOGS, TASKS


def list_tasks_for_user(user_id: str) -> List[Task]:
    return sorted(
        [t for t in TASKS.values() if t.assigned_to == user_id],
        key=lambda t: (t.priority, t.sequence),
    )


def get_task(task_id: str) -> Optional[Task]:
    return TASKS.get(task_id.upper())


def get_next_task(user_id: str) -> Optional[Task]:
    pending = [
        t
        for t in TASKS.values()
        if t.assigned_to == user_id and t.status == TaskStatus.PENDING
    ]
    if not pending:
        return None
    return sorted(pending, key=lambda t: (t.priority, t.sequence))[0]


def update_task_status(
    task_id: str,
    update: TaskStatusUpdate,
    user_id: str,
) -> Optional[Task]:
    task = TASKS.get(task_id.upper())
    if not task:
        return None

    task.status = update.status
    if update.exception_note:
        task.exception_note = update.exception_note
    task.updated_at = datetime.utcnow()

    AUDIT_LOGS.append(
        AuditLog(
            log_id=str(uuid4()),
            user_id=user_id,
            action="update_task_status",
            entity_type="task",
            entity_id=task_id,
            details={
                "new_status": update.status,
                "exception_note": update.exception_note,
            },
        )
    )
    return task


def log_exception(
    task_id: str,
    note: str,
    user_id: str,
) -> Optional[Task]:
    return update_task_status(
        task_id,
        TaskStatusUpdate(status=TaskStatus.EXCEPTION, exception_note=note),
        user_id,
    )


def create_exception_task(
    description: str,
    location: str,
    assigned_to: str,
    shipment_id: Optional[str] = None,
) -> Task:
    task_id = f"TSK{str(uuid4())[:8].upper()}"
    task = Task(
        task_id=task_id,
        task_type=TaskType.EXCEPTION_LOG,
        shipment_id=shipment_id,
        assigned_to=assigned_to,
        description=description,
        location=location,
        status=TaskStatus.IN_PROGRESS,
        priority=1,
    )
    TASKS[task_id] = task
    return task
