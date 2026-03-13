"""
Data models for shipments, tasks, voice commands, users, and audit logs.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ShipmentStatus(str, Enum):
    PENDING = "pending"
    PICKED = "picked"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"
    RETURNED = "returned"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    EXCEPTION = "exception"


class TaskType(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
    PUTAWAY = "putaway"
    LOADING = "loading"
    EXCEPTION_LOG = "exception_log"


class UserRole(str, Enum):
    DRIVER = "driver"
    WAREHOUSE = "warehouse"
    DISPATCHER = "dispatcher"
    ADMIN = "admin"


class VoiceIntent(str, Enum):
    TRACK_SHIPMENT = "track_shipment"
    UPDATE_STATUS = "update_status"
    NEXT_STOP = "next_stop"
    MARK_PICKED = "mark_picked"
    MARK_DELIVERED = "mark_delivered"
    LOG_EXCEPTION = "log_exception"
    LIST_TASKS = "list_tasks"
    SEND_NOTIFICATION = "send_notification"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Shipment models
# ---------------------------------------------------------------------------


class Stop(BaseModel):
    stop_number: int
    address: str
    consignee_name: str
    consignee_phone: Optional[str] = None
    eta: Optional[datetime] = None
    status: ShipmentStatus = ShipmentStatus.PENDING
    special_instructions: Optional[str] = None


class Shipment(BaseModel):
    shipment_id: str
    tracking_number: str
    customer_name: str
    origin: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.PENDING
    eta: Optional[datetime] = None
    current_location: Optional[str] = None
    driver_id: Optional[str] = None
    route: List[Stop] = Field(default_factory=list)
    weight_kg: Optional[float] = None
    special_instructions: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ShipmentStatusUpdate(BaseModel):
    status: ShipmentStatus
    location: Optional[str] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Task models
# ---------------------------------------------------------------------------


class Task(BaseModel):
    task_id: str
    task_type: TaskType
    shipment_id: Optional[str] = None
    assigned_to: str
    description: str
    location: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=1, ge=1, le=5)
    sequence: int = Field(default=1)
    exception_note: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    exception_note: Optional[str] = None


# ---------------------------------------------------------------------------
# Voice models
# ---------------------------------------------------------------------------


class VoiceCommandRequest(BaseModel):
    text: str = Field(..., description="Transcribed voice command text")
    user_id: str
    role: UserRole = UserRole.DRIVER


class VoiceCommandResponse(BaseModel):
    intent: VoiceIntent
    entities: dict = Field(default_factory=dict)
    spoken_response: str
    action_taken: Optional[str] = None
    data: Optional[object] = None


class AuditLog(BaseModel):
    log_id: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Auth models
# ---------------------------------------------------------------------------


class User(BaseModel):
    user_id: str
    username: str
    role: UserRole
    full_name: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    username: str
    password: str
