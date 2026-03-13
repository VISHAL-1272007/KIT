"""
Tests for shipment and task services.
"""

import pytest
from app.models.schemas import ShipmentStatus, ShipmentStatusUpdate, TaskStatus, TaskStatusUpdate
from app.services import shipment_service, task_service


class TestShipmentService:
    def test_get_shipment_exists(self):
        shipment = shipment_service.get_shipment("SHP001")
        assert shipment is not None
        assert shipment.shipment_id == "SHP001"

    def test_get_shipment_not_found(self):
        assert shipment_service.get_shipment("SHP999") is None

    def test_find_by_tracking(self):
        shipment = shipment_service.find_by_tracking("TRK-2026-001")
        assert shipment is not None
        assert shipment.customer_name == "Acme Corp"

    def test_find_by_tracking_case_insensitive(self):
        shipment = shipment_service.find_by_tracking("trk-2026-001")
        assert shipment is not None

    def test_find_by_customer(self):
        results = shipment_service.find_by_customer("Acme")
        assert len(results) >= 1
        assert all("Acme" in r.customer_name for r in results)

    def test_find_by_driver(self):
        results = shipment_service.find_by_driver("DRV001")
        assert len(results) >= 1
        assert all(r.driver_id == "DRV001" for r in results)

    def test_update_status(self):
        from app.models.store import SHIPMENTS
        # Reset to original status after test
        original = SHIPMENTS["SHP002"].status
        updated = shipment_service.update_status(
            "SHP002",
            ShipmentStatusUpdate(status=ShipmentStatus.DELIVERED),
            "TEST_USER",
        )
        assert updated is not None
        assert updated.status == ShipmentStatus.DELIVERED
        # Restore
        SHIPMENTS["SHP002"].status = original

    def test_update_status_not_found(self):
        result = shipment_service.update_status(
            "SHP999",
            ShipmentStatusUpdate(status=ShipmentStatus.DELIVERED),
            "TEST_USER",
        )
        assert result is None

    def test_get_next_stop(self):
        # DRV001 has in-transit shipment SHP001 with a pending stop
        from app.models.store import SHIPMENTS
        from app.models.schemas import ShipmentStatus
        SHIPMENTS["SHP001"].status = ShipmentStatus.IN_TRANSIT
        stop_data = shipment_service.get_next_stop("DRV001")
        assert stop_data is not None
        assert "stop" in stop_data


class TestTaskService:
    def test_list_tasks_for_user(self):
        tasks = task_service.list_tasks_for_user("DRV001")
        assert len(tasks) >= 1
        assert all(t.assigned_to == "DRV001" for t in tasks)

    def test_get_task_exists(self):
        task = task_service.get_task("TSK003")
        assert task is not None
        assert task.task_id == "TSK003"

    def test_get_task_not_found(self):
        assert task_service.get_task("TSK999") is None

    def test_update_task_status(self):
        from app.models.store import TASKS
        original = TASKS["TSK003"].status
        updated = task_service.update_task_status(
            "TSK003",
            TaskStatusUpdate(status=TaskStatus.COMPLETED),
            "TEST_USER",
        )
        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED
        # Restore
        TASKS["TSK003"].status = original

    def test_log_exception(self):
        from app.models.store import TASKS
        original = TASKS["TSK003"].status
        updated = task_service.log_exception("TSK003", "Test exception", "TEST_USER")
        assert updated is not None
        assert updated.status == TaskStatus.EXCEPTION
        assert updated.exception_note == "Test exception"
        # Restore
        TASKS["TSK003"].status = original
        TASKS["TSK003"].exception_note = None

    def test_create_exception_task(self):
        task = task_service.create_exception_task(
            description="Test exception task",
            location="Bay 1",
            assigned_to="DRV001",
            shipment_id="SHP001",
        )
        assert task is not None
        assert task.assigned_to == "DRV001"
        assert task.shipment_id == "SHP001"
        # Clean up
        from app.models.store import TASKS
        TASKS.pop(task.task_id, None)
