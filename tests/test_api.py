"""
Integration tests for the FastAPI application endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_token(username: str, password: str) -> str:
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------


class TestAuth:
    def test_login_success(self):
        resp = client.post("/auth/login", json={"username": "driver1", "password": "driver123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self):
        resp = client.post("/auth/login", json={"username": "driver1", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_user(self):
        resp = client.post("/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401

    def test_protected_endpoint_requires_token(self):
        resp = client.get("/shipments/")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Shipment tests
# ---------------------------------------------------------------------------


class TestShipments:
    @pytest.fixture(autouse=True)
    def auth_headers(self):
        token = _get_token("dispatcher1", "dispatch123")
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_list_shipments(self):
        resp = client.get("/shipments/", headers=self.headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 3

    def test_get_shipment_by_id(self):
        resp = client.get("/shipments/SHP001", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["shipment_id"] == "SHP001"
        assert data["customer_name"] == "Acme Corp"

    def test_get_shipment_not_found(self):
        resp = client.get("/shipments/SHP999", headers=self.headers)
        assert resp.status_code == 404

    def test_search_by_tracking(self):
        resp = client.get(
            "/shipments/search?tracking=TRK-2026-001", headers=self.headers
        )
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert results[0]["tracking_number"] == "TRK-2026-001"

    def test_search_by_customer(self):
        resp = client.get(
            "/shipments/search?customer=Acme", headers=self.headers
        )
        assert resp.status_code == 200
        results = resp.json()
        assert any("Acme" in r["customer_name"] for r in results)

    def test_update_shipment_status(self):
        resp = client.patch(
            "/shipments/SHP003/status",
            json={"status": "picked", "note": "test pick"},
            headers=self.headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "picked"


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------


class TestTasks:
    @pytest.fixture(autouse=True)
    def auth_headers(self):
        token = _get_token("driver1", "driver123")
        self.headers = {"Authorization": f"Bearer {token}"}

    def test_list_my_tasks(self):
        resp = client.get("/tasks/", headers=self.headers)
        assert resp.status_code == 200
        tasks = resp.json()
        assert isinstance(tasks, list)
        # driver1 (DRV001) has tasks TSK001 and TSK002
        assert len(tasks) >= 2

    def test_get_next_task(self):
        resp = client.get("/tasks/next", headers=self.headers)
        # DRV001 has a PENDING task TSK001
        assert resp.status_code == 200
        task = resp.json()
        assert task["status"] == "pending"
        assert task["assigned_to"] == "DRV001"

    def test_get_task_by_id(self):
        resp = client.get("/tasks/TSK001", headers=self.headers)
        assert resp.status_code == 200
        assert resp.json()["task_id"] == "TSK001"

    def test_update_task_status(self):
        resp = client.patch(
            "/tasks/TSK001/status",
            json={"status": "completed"},
            headers=self.headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


# ---------------------------------------------------------------------------
# Voice command tests
# ---------------------------------------------------------------------------


class TestVoiceCommand:
    @pytest.fixture(autouse=True)
    def auth_headers(self):
        token = _get_token("driver1", "driver123")
        self.headers = {"Authorization": f"Bearer {token}"}

    def _cmd(self, text: str) -> dict:
        resp = client.post(
            "/voice/command",
            json={"text": text, "user_id": "DRV001"},
            headers=self.headers,
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    def test_track_shipment_voice(self):
        result = self._cmd("What is the status of shipment SHP001?")
        assert result["intent"] == "track_shipment"
        assert "spoken_response" in result
        assert len(result["spoken_response"]) > 0

    def test_next_stop_voice(self):
        result = self._cmd("What is my next stop?")
        assert result["intent"] == "next_stop"
        assert "spoken_response" in result

    def test_list_tasks_voice(self):
        result = self._cmd("List my tasks")
        assert result["intent"] == "list_tasks"

    def test_log_exception_voice(self):
        result = self._cmd("Package is damaged for shipment SHP002")
        assert result["intent"] == "log_exception"
        assert "exception_logged" == result.get("action_taken")

    def test_mark_picked_voice(self):
        result = self._cmd("Mark shipment SHP003 as picked")
        assert result["intent"] == "mark_picked"

    def test_unknown_command_voice(self):
        result = self._cmd("Tell me a joke")
        assert result["intent"] == "unknown"
        assert "spoken_response" in result

    def test_health_check(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
