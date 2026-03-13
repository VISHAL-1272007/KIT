"""
Shipment tracking router.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.schemas import Shipment, ShipmentStatusUpdate, TokenData
from app.routers.deps import get_current_user
from app.services import shipment_service

router = APIRouter()


@router.get("/", response_model=List[Shipment])
def list_shipments(current_user: TokenData = Depends(get_current_user)):
    """List all shipments (admin/dispatcher) or only the caller's shipments (driver)."""
    if current_user.role and current_user.role.value in ("driver",):
        return shipment_service.find_by_driver(current_user.user_id)
    return shipment_service.list_shipments()


@router.get("/search", response_model=List[Shipment])
def search_shipments(
    customer: str = Query(None, description="Customer name to search"),
    tracking: str = Query(None, description="Tracking number to search"),
    current_user: TokenData = Depends(get_current_user),
):
    """Search shipments by customer name or tracking number."""
    if tracking:
        result = shipment_service.find_by_tracking(tracking)
        return [result] if result else []
    if customer:
        return shipment_service.find_by_customer(customer)
    return shipment_service.list_shipments()


@router.get("/next-stop", response_model=dict)
def next_stop(current_user: TokenData = Depends(get_current_user)):
    """Return the next pending delivery stop for the authenticated driver."""
    stop = shipment_service.get_next_stop(current_user.user_id)
    if not stop:
        return {"message": "No pending stops found", "stop": None}
    return stop


@router.get("/{shipment_id}", response_model=Shipment)
def get_shipment(shipment_id: str, current_user: TokenData = Depends(get_current_user)):
    """Get details for a specific shipment by ID or tracking number."""
    shipment = shipment_service.get_shipment(shipment_id) or shipment_service.find_by_tracking(
        shipment_id
    )
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment


@router.patch("/{shipment_id}/status", response_model=Shipment)
def update_shipment_status(
    shipment_id: str,
    update: ShipmentStatusUpdate,
    current_user: TokenData = Depends(get_current_user),
):
    """Update the status of a shipment (supports voice-initiated updates)."""
    updated = shipment_service.update_status(shipment_id, update, current_user.user_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return updated
