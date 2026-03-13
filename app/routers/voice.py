"""
Voice command router – the core hands-free interface.
"""

from fastapi import APIRouter, Depends

from app.models.schemas import AuditLog, TokenData, VoiceCommandRequest, VoiceCommandResponse
from app.models.store import AUDIT_LOGS
from app.routers.deps import get_current_user
from app.voice.processor import process_voice_command

router = APIRouter()


@router.post("/command", response_model=VoiceCommandResponse)
def voice_command(
    request: VoiceCommandRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Process a natural-language voice command.

    The `text` field contains the transcribed speech. The assistant will
    classify the intent, extract entities, execute the appropriate action,
    and return a `spoken_response` that should be read aloud to the worker.

    **Example commands:**
    - "What is the status of shipment SHP001?"
    - "Mark order TRK-2026-003 as picked"
    - "What's my next stop?"
    - "List my tasks"
    - "Package damaged for shipment SHP002"
    - "Send delay notification to customer"
    """
    # Enforce that the request user matches the authenticated user
    request.user_id = current_user.user_id
    if current_user.role:
        request.role = current_user.role

    response = process_voice_command(request)
    return response


@router.get("/audit-log", response_model=list)
def get_audit_log(current_user: TokenData = Depends(get_current_user)):
    """Return all voice-initiated audit log entries (admin/dispatcher only)."""
    if current_user.role and current_user.role.value not in ("admin", "dispatcher"):
        return [
            entry
            for entry in AUDIT_LOGS
            if entry.user_id == current_user.user_id
        ]
    return [entry.model_dump(mode="json") for entry in AUDIT_LOGS]
