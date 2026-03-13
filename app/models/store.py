"""
In-memory data store with seed data for the logistics assistant.
In production this would be replaced by a real database.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from app.models.schemas import (
    Shipment,
    ShipmentStatus,
    Stop,
    Task,
    TaskStatus,
    TaskType,
    User,
    UserRole,
    AuditLog,
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ---------------------------------------------------------------------------
# Seed shipments
# ---------------------------------------------------------------------------

_now = datetime.utcnow()

SHIPMENTS: Dict[str, Shipment] = {
    "SHP001": Shipment(
        shipment_id="SHP001",
        tracking_number="TRK-2026-001",
        customer_name="Acme Corp",
        origin="Chennai Warehouse",
        destination="Coimbatore Hub",
        status=ShipmentStatus.IN_TRANSIT,
        eta=_now + timedelta(hours=3),
        current_location="Salem Checkpoint",
        driver_id="DRV001",
        weight_kg=120.5,
        special_instructions="Fragile – handle with care",
        route=[
            Stop(
                stop_number=1,
                address="Salem Checkpoint",
                consignee_name="Transit Hub A",
                status=ShipmentStatus.DELIVERED,
            ),
            Stop(
                stop_number=2,
                address="Coimbatore Hub",
                consignee_name="Raj Kumar",
                consignee_phone="+91-9876543210",
                eta=_now + timedelta(hours=3),
                status=ShipmentStatus.PENDING,
                special_instructions="Call before delivery",
            ),
        ],
    ),
    "SHP002": Shipment(
        shipment_id="SHP002",
        tracking_number="TRK-2026-002",
        customer_name="Global Traders",
        origin="Mumbai Port",
        destination="Delhi Distribution",
        status=ShipmentStatus.OUT_FOR_DELIVERY,
        eta=_now + timedelta(hours=1),
        current_location="Delhi Ring Road",
        driver_id="DRV002",
        weight_kg=340.0,
        route=[
            Stop(
                stop_number=1,
                address="Delhi Distribution Centre",
                consignee_name="Priya Sharma",
                consignee_phone="+91-9123456780",
                eta=_now + timedelta(hours=1),
                status=ShipmentStatus.PENDING,
            ),
        ],
    ),
    "SHP003": Shipment(
        shipment_id="SHP003",
        tracking_number="TRK-2026-003",
        customer_name="TechZone Ltd",
        origin="Bengaluru Tech Park",
        destination="Hyderabad Office",
        status=ShipmentStatus.PENDING,
        eta=_now + timedelta(hours=6),
        driver_id="DRV001",
        weight_kg=55.0,
        special_instructions="Electronics – keep dry",
        route=[
            Stop(
                stop_number=1,
                address="Hyderabad Office Park",
                consignee_name="Anand Reddy",
                consignee_phone="+91-9001234567",
                eta=_now + timedelta(hours=6),
                status=ShipmentStatus.PENDING,
            ),
        ],
    ),
}

# ---------------------------------------------------------------------------
# Seed tasks
# ---------------------------------------------------------------------------

TASKS: Dict[str, Task] = {
    "TSK001": Task(
        task_id="TSK001",
        task_type=TaskType.PICKUP,
        shipment_id="SHP003",
        assigned_to="DRV001",
        description="Pick up shipment TRK-2026-003 from Bengaluru Tech Park",
        location="Bengaluru Tech Park – Bay 4",
        status=TaskStatus.PENDING,
        priority=2,
        sequence=1,
    ),
    "TSK002": Task(
        task_id="TSK002",
        task_type=TaskType.DELIVERY,
        shipment_id="SHP001",
        assigned_to="DRV001",
        description="Deliver TRK-2026-001 to Coimbatore Hub",
        location="Coimbatore Hub – Gate 2",
        status=TaskStatus.IN_PROGRESS,
        priority=1,
        sequence=2,
    ),
    "TSK003": Task(
        task_id="TSK003",
        task_type=TaskType.PUTAWAY,
        shipment_id="SHP002",
        assigned_to="WH001",
        description="Putaway shipment TRK-2026-002 in Rack C4",
        location="Warehouse A – Rack C4",
        status=TaskStatus.PENDING,
        priority=3,
        sequence=1,
    ),
}

# ---------------------------------------------------------------------------
# Seed users
# ---------------------------------------------------------------------------

USERS: Dict[str, User] = {
    "DRV001": User(
        user_id="DRV001",
        username="driver1",
        role=UserRole.DRIVER,
        full_name="Murugan Kumar",
        hashed_password=pwd_context.hash("driver123"),
    ),
    "DRV002": User(
        user_id="DRV002",
        username="driver2",
        role=UserRole.DRIVER,
        full_name="Selvam Raja",
        hashed_password=pwd_context.hash("driver456"),
    ),
    "WH001": User(
        user_id="WH001",
        username="warehouse1",
        role=UserRole.WAREHOUSE,
        full_name="Lakshmi Devi",
        hashed_password=pwd_context.hash("warehouse123"),
    ),
    "DISP001": User(
        user_id="DISP001",
        username="dispatcher1",
        role=UserRole.DISPATCHER,
        full_name="Venkat Subramanian",
        hashed_password=pwd_context.hash("dispatch123"),
    ),
    "ADMIN001": User(
        user_id="ADMIN001",
        username="admin",
        role=UserRole.ADMIN,
        full_name="System Admin",
        hashed_password=pwd_context.hash("admin123"),
    ),
}

USERS_BY_USERNAME: Dict[str, User] = {u.username: u for u in USERS.values()}

# ---------------------------------------------------------------------------
# Audit log store
# ---------------------------------------------------------------------------

AUDIT_LOGS: List[AuditLog] = []
