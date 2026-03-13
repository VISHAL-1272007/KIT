"""
NLU engine for logistics voice commands.

Uses rule-based intent classification and entity extraction.
In production, this is replaced by a fine-tuned transformer model
(see training/train_nlu_model.py for the HuggingFace training pipeline).
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

from app.models.schemas import VoiceIntent

# ---------------------------------------------------------------------------
# Intent patterns (order matters – most specific first)
# ---------------------------------------------------------------------------

_INTENT_PATTERNS = [
    # Mark delivered (before generic track so "mark ... delivered" wins)
    (
        VoiceIntent.MARK_DELIVERED,
        re.compile(
            r"(mark|set|confirm|complete)\s+"
            r"(shipment|order|task|delivery)?\s*"
            r"(?P<id>[A-Z0-9\-]{3,})?\s*"
            r"(as\s+)?(delivered|done|complete|completed)",
            re.IGNORECASE,
        ),
    ),
    # Mark picked (before generic track)
    (
        VoiceIntent.MARK_PICKED,
        re.compile(
            r"(mark|set|confirm)\s+"
            r"(shipment|order|task|package)?\s*"
            r"(?P<id>[A-Z0-9\-]{3,})?\s*"
            r"(as\s+)?(picked|picked up|collected)",
            re.IGNORECASE,
        ),
    ),
    # Update status
    (
        VoiceIntent.UPDATE_STATUS,
        re.compile(
            r"(update|change)\s+status\s+"
            r"(of\s+)?(shipment|order)?\s*"
            r"(?P<id>[A-Z0-9\-]{3,})",
            re.IGNORECASE,
        ),
    ),
    # Log exception – explicit keywords
    (
        VoiceIntent.LOG_EXCEPTION,
        re.compile(
            r"(log|report|flag|raise)\s+(exception|issue|problem|damage|incident)"
            r"(\s+for\s+(shipment|order|package)?\s*(?P<id>[A-Z0-9\-]{3,}))?",
            re.IGNORECASE,
        ),
    ),
    # Log exception – "package/item/parcel is damaged/broken/…"
    (
        VoiceIntent.LOG_EXCEPTION,
        re.compile(
            r"(package|item|parcel)\s+(is\s+)?(damaged|broken|missing|lost|wet|crushed)",
            re.IGNORECASE,
        ),
    ),
    (
        VoiceIntent.LOG_EXCEPTION,
        re.compile(
            r"customer\s+(not available|not home|refused|absent)",
            re.IGNORECASE,
        ),
    ),
    # Next stop
    (
        VoiceIntent.NEXT_STOP,
        re.compile(
            r"(what('s| is) my )?(next|upcoming)\s+(stop|delivery|destination|location)",
            re.IGNORECASE,
        ),
    ),
    (
        VoiceIntent.NEXT_STOP,
        re.compile(r"where (do i|should i) go next", re.IGNORECASE),
    ),
    # List tasks
    (
        VoiceIntent.LIST_TASKS,
        re.compile(
            r"(list|show|what are|give me|tell me)\s+(my\s+)?"
            r"(tasks|jobs|assignments|to.?do|work list)",
            re.IGNORECASE,
        ),
    ),
    (
        VoiceIntent.LIST_TASKS,
        re.compile(r"what (should|do) i (do|pick|deliver) (next|now|today)", re.IGNORECASE),
    ),
    # Send notification
    (
        VoiceIntent.SEND_NOTIFICATION,
        re.compile(
            r"(send|notify|alert|inform|call)\s+"
            r"(the\s+)?(customer|consignee|client|receiver|recipient|dispatch)",
            re.IGNORECASE,
        ),
    ),
    (
        VoiceIntent.SEND_NOTIFICATION,
        re.compile(r"send\s+(delay|late|eta)\s+(notification|alert|message|update)", re.IGNORECASE),
    ),
    # Track shipment – keyword + optional filler + optional type word + ID
    (
        VoiceIntent.TRACK_SHIPMENT,
        re.compile(
            r"(track|status|where is|find|check|locate)"
            r"(\s+\w+){0,3}\s+"
            r"(shipment|order|package|parcel|delivery)?\s*"
            r"(?P<id>[A-Z0-9\-]{4,})",
            re.IGNORECASE,
        ),
    ),
    # Track shipment – "status of shipment ID" style
    (
        VoiceIntent.TRACK_SHIPMENT,
        re.compile(
            r"(status|tracking|info|information|update)\s+(of|for|on)\s+"
            r"(shipment|order|package|parcel)?\s*"
            r"(?P<id>[A-Z0-9\-]{4,})",
            re.IGNORECASE,
        ),
    ),
    # Track shipment – plain ID anywhere after track/check keyword
    (
        VoiceIntent.TRACK_SHIPMENT,
        re.compile(
            r"(track|find|locate|check)\s+(?P<id>[A-Z0-9\-]{4,})",
            re.IGNORECASE,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Entity extractors
# ---------------------------------------------------------------------------

_SHIPMENT_ID_RE = re.compile(r"\b(SHP\d{3,}|TRK-\d{4}-\d{3,})\b", re.IGNORECASE)
_TASK_ID_RE = re.compile(r"\bTSK[A-Z0-9]{3,}\b", re.IGNORECASE)
_EXCEPTION_NOTE_KEYWORDS = {
    "damaged": "package damaged",
    "broken": "package broken",
    "missing": "package missing",
    "lost": "package lost",
    "wet": "package wet",
    "crushed": "package crushed",
    "not available": "customer not available",
    "not home": "customer not home",
    "refused": "customer refused delivery",
    "absent": "customer absent",
}


def extract_entities(text: str) -> dict:
    entities: dict = {}

    # Shipment / tracking ID
    m = _SHIPMENT_ID_RE.search(text)
    if m:
        entities["shipment_id"] = m.group(0).upper()

    # Task ID
    m = _TASK_ID_RE.search(text)
    if m:
        entities["task_id"] = m.group(0).upper()

    # Exception note
    lower = text.lower()
    for keyword, note in _EXCEPTION_NOTE_KEYWORDS.items():
        if keyword in lower:
            entities["exception_note"] = note
            break

    return entities


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def classify_intent(text: str) -> Tuple[VoiceIntent, dict]:
    """Return (intent, entities) for a free-text voice command."""
    for intent, pattern in _INTENT_PATTERNS:
        match = pattern.search(text)
        if match:
            entities = extract_entities(text)
            # Also pull inline ID from the pattern group if available
            try:
                inline_id = match.group("id")
                if inline_id and "shipment_id" not in entities:
                    entities["shipment_id"] = inline_id.upper()
            except IndexError:
                pass
            return intent, entities

    return VoiceIntent.UNKNOWN, extract_entities(text)
