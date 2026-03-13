"""
Tests for the NLU intent classification engine.
"""

import pytest
from app.models.schemas import VoiceIntent
from app.voice.nlu_engine import classify_intent, extract_entities


class TestIntentClassification:
    def test_track_shipment_by_id(self):
        intent, entities = classify_intent("What is the status of shipment SHP001?")
        assert intent == VoiceIntent.TRACK_SHIPMENT
        assert "SHP001" in entities.get("shipment_id", "")

    def test_track_shipment_by_tracking_number(self):
        intent, entities = classify_intent("Track order TRK-2026-001")
        assert intent == VoiceIntent.TRACK_SHIPMENT

    def test_mark_picked(self):
        intent, entities = classify_intent("Mark shipment SHP003 as picked")
        assert intent == VoiceIntent.MARK_PICKED
        assert "SHP003" in entities.get("shipment_id", "")

    def test_mark_delivered(self):
        intent, entities = classify_intent("Mark shipment SHP001 as delivered")
        assert intent == VoiceIntent.MARK_DELIVERED
        assert "SHP001" in entities.get("shipment_id", "")

    def test_next_stop(self):
        intent, _ = classify_intent("What is my next stop?")
        assert intent == VoiceIntent.NEXT_STOP

    def test_next_stop_variant(self):
        intent, _ = classify_intent("Where do I go next?")
        assert intent == VoiceIntent.NEXT_STOP

    def test_list_tasks(self):
        intent, _ = classify_intent("List my tasks")
        assert intent == VoiceIntent.LIST_TASKS

    def test_list_tasks_variant(self):
        intent, _ = classify_intent("What should I do next?")
        assert intent == VoiceIntent.LIST_TASKS

    def test_log_exception_damaged(self):
        intent, entities = classify_intent("Package is damaged for shipment SHP002")
        assert intent == VoiceIntent.LOG_EXCEPTION
        assert "package damaged" in entities.get("exception_note", "")

    def test_log_exception_customer_not_available(self):
        intent, entities = classify_intent("Customer not available")
        assert intent == VoiceIntent.LOG_EXCEPTION
        assert "customer not available" in entities.get("exception_note", "")

    def test_send_notification(self):
        intent, _ = classify_intent("Send delay notification to customer")
        assert intent == VoiceIntent.SEND_NOTIFICATION

    def test_send_notification_variant(self):
        intent, _ = classify_intent("Notify consignee")
        assert intent == VoiceIntent.SEND_NOTIFICATION

    def test_unknown_intent(self):
        intent, _ = classify_intent("Play some music")
        assert intent == VoiceIntent.UNKNOWN

    def test_case_insensitive(self):
        intent, _ = classify_intent("WHAT IS MY NEXT STOP")
        assert intent == VoiceIntent.NEXT_STOP


class TestEntityExtraction:
    def test_extract_shipment_id(self):
        entities = extract_entities("Check shipment SHP001 please")
        assert entities["shipment_id"] == "SHP001"

    def test_extract_tracking_number(self):
        entities = extract_entities("Track TRK-2026-002 for me")
        assert entities["shipment_id"] == "TRK-2026-002"

    def test_extract_exception_note_damaged(self):
        entities = extract_entities("The package is damaged")
        assert "damaged" in entities.get("exception_note", "")

    def test_extract_exception_note_customer_refused(self):
        entities = extract_entities("Customer refused the delivery")
        assert "refused" in entities.get("exception_note", "")

    def test_no_entities_in_simple_query(self):
        entities = extract_entities("What is my next stop?")
        assert "shipment_id" not in entities
        assert "exception_note" not in entities
