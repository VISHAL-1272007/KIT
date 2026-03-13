"""
Shipment tracking service – read and update shipment records.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from app.models.schemas import AuditLog, Shipment, ShipmentStatus, ShipmentStatusUpdate
from app.models.store import AUDIT_LOGS, SHIPMENTS


def get_shipment(shipment_id: str) -> Optional[Shipment]:
    return SHIPMENTS.get(shipment_id.upper())


def find_by_tracking(tracking_number: str) -> Optional[Shipment]:
    for s in SHIPMENTS.values():
        if s.tracking_number.upper() == tracking_number.upper():
            return s
    return None


def find_by_customer(customer_name: str) -> List[Shipment]:
    name_lower = customer_name.lower()
    return [s for s in SHIPMENTS.values() if name_lower in s.customer_name.lower()]


def find_by_driver(driver_id: str) -> List[Shipment]:
    return [s for s in SHIPMENTS.values() if s.driver_id == driver_id]


def list_shipments() -> List[Shipment]:
    return list(SHIPMENTS.values())


def update_status(
    shipment_id: str,
    update: ShipmentStatusUpdate,
    user_id: str,
) -> Optional[Shipment]:
    shipment = SHIPMENTS.get(shipment_id.upper())
    if not shipment:
        return None

    shipment.status = update.status
    if update.location:
        shipment.current_location = update.location
    shipment.updated_at = datetime.utcnow()

    AUDIT_LOGS.append(
        AuditLog(
            log_id=str(uuid4()),
            user_id=user_id,
            action="update_shipment_status",
            entity_type="shipment",
            entity_id=shipment_id,
            details={
                "new_status": update.status,
                "location": update.location,
                "note": update.note,
            },
        )
    )
    return shipment


def get_next_stop(driver_id: str) -> Optional[dict]:
    """Return the next pending stop for a driver across all their shipments."""
    driver_shipments = find_by_driver(driver_id)
    for shipment in driver_shipments:
        if shipment.status in (
            ShipmentStatus.IN_TRANSIT,
            ShipmentStatus.OUT_FOR_DELIVERY,
            ShipmentStatus.PENDING,
        ):
            for stop in shipment.route:
                if stop.status == ShipmentStatus.PENDING:
                    return {
                        "shipment_id": shipment.shipment_id,
                        "tracking_number": shipment.tracking_number,
                        "stop": stop.model_dump(),
                        "special_instructions": shipment.special_instructions,
                    }
    return None
