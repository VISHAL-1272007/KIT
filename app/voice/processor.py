"""
Voice command processor – orchestrates NLU, service calls, and response generation.
"""

from __future__ import annotations

from app.models.schemas import (
    ShipmentStatus,
    ShipmentStatusUpdate,
    TaskStatus,
    TaskStatusUpdate,
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceIntent,
)
from app.services import shipment_service, task_service
from app.voice.nlu_engine import classify_intent


# ---------------------------------------------------------------------------
# Response templates
# ---------------------------------------------------------------------------


def _fmt_shipment(s) -> str:
    eta_str = s.eta.strftime("%I:%M %p") if s.eta else "unknown"
    loc = s.current_location or s.origin
    return (
        f"Shipment {s.tracking_number} for {s.customer_name} is currently "
        f"{s.status.replace('_', ' ')} at {loc}. Estimated delivery: {eta_str}."
    )


def _fmt_stop(stop_data: dict) -> str:
    stop = stop_data["stop"]
    trk = stop_data["tracking_number"]
    eta_str = ""
    if stop.get("eta"):
        from datetime import datetime
        try:
            eta_dt = datetime.fromisoformat(str(stop["eta"]))
            eta_str = f" ETA {eta_dt.strftime('%I:%M %p')}."
        except Exception:
            pass
    instructions = ""
    if stop_data.get("special_instructions"):
        instructions = f" Note: {stop_data['special_instructions']}."
    return (
        f"Your next stop is {stop['address']} for {stop['consignee_name']} "
        f"on shipment {trk}.{eta_str}{instructions}"
    )


# ---------------------------------------------------------------------------
# Intent handlers
# ---------------------------------------------------------------------------


def _handle_track(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    sid = entities.get("shipment_id")
    shipment = None
    if sid:
        shipment = shipment_service.get_shipment(sid) or shipment_service.find_by_tracking(sid)
    if not shipment:
        return VoiceCommandResponse(
            intent=VoiceIntent.TRACK_SHIPMENT,
            entities=entities,
            spoken_response="I could not find that shipment. Please check the ID and try again.",
        )
    return VoiceCommandResponse(
        intent=VoiceIntent.TRACK_SHIPMENT,
        entities=entities,
        spoken_response=_fmt_shipment(shipment),
        data=shipment.model_dump(mode="json"),
    )


def _handle_mark_picked(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    sid = entities.get("shipment_id")
    if not sid:
        return VoiceCommandResponse(
            intent=VoiceIntent.MARK_PICKED,
            entities=entities,
            spoken_response="Please specify the shipment ID to mark as picked.",
        )
    updated = shipment_service.update_status(
        sid,
        ShipmentStatusUpdate(status=ShipmentStatus.PICKED, note="Marked picked via voice"),
        req.user_id,
    )
    if not updated:
        return VoiceCommandResponse(
            intent=VoiceIntent.MARK_PICKED,
            entities=entities,
            spoken_response=f"Shipment {sid} not found.",
        )
    return VoiceCommandResponse(
        intent=VoiceIntent.MARK_PICKED,
        entities=entities,
        spoken_response=f"Shipment {updated.tracking_number} has been marked as picked.",
        action_taken="status_updated",
        data=updated.model_dump(mode="json"),
    )


def _handle_mark_delivered(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    sid = entities.get("shipment_id") or entities.get("task_id")

    # Try task first
    if sid and sid.startswith("TSK"):
        updated_task = task_service.update_task_status(
            sid,
            TaskStatusUpdate(status=TaskStatus.COMPLETED),
            req.user_id,
        )
        if updated_task:
            return VoiceCommandResponse(
                intent=VoiceIntent.MARK_DELIVERED,
                entities=entities,
                spoken_response=f"Task {sid} has been marked as completed.",
                action_taken="task_completed",
                data=updated_task.model_dump(mode="json"),
            )

    # Fall back to shipment
    if not sid:
        return VoiceCommandResponse(
            intent=VoiceIntent.MARK_DELIVERED,
            entities=entities,
            spoken_response="Please specify the shipment or task ID to mark as delivered.",
        )
    updated = shipment_service.update_status(
        sid,
        ShipmentStatusUpdate(status=ShipmentStatus.DELIVERED, note="Marked delivered via voice"),
        req.user_id,
    )
    if not updated:
        return VoiceCommandResponse(
            intent=VoiceIntent.MARK_DELIVERED,
            entities=entities,
            spoken_response=f"Shipment {sid} not found.",
        )
    return VoiceCommandResponse(
        intent=VoiceIntent.MARK_DELIVERED,
        entities=entities,
        spoken_response=f"Shipment {updated.tracking_number} has been marked as delivered. Great work!",
        action_taken="status_updated",
        data=updated.model_dump(mode="json"),
    )


def _handle_next_stop(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    stop_data = shipment_service.get_next_stop(req.user_id)
    if not stop_data:
        return VoiceCommandResponse(
            intent=VoiceIntent.NEXT_STOP,
            entities=entities,
            spoken_response="You have no more pending stops. All deliveries are complete!",
        )
    return VoiceCommandResponse(
        intent=VoiceIntent.NEXT_STOP,
        entities=entities,
        spoken_response=_fmt_stop(stop_data),
        data=stop_data,
    )


def _handle_list_tasks(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    tasks = task_service.list_tasks_for_user(req.user_id)
    pending = [t for t in tasks if t.status == TaskStatus.PENDING]
    if not pending:
        return VoiceCommandResponse(
            intent=VoiceIntent.LIST_TASKS,
            entities=entities,
            spoken_response="You have no pending tasks right now.",
            data=[],
        )
    names = "; ".join(f"Task {t.task_id}: {t.description}" for t in pending[:5])
    spoken = f"You have {len(pending)} pending task(s). {names}."
    return VoiceCommandResponse(
        intent=VoiceIntent.LIST_TASKS,
        entities=entities,
        spoken_response=spoken,
        data=[t.model_dump(mode="json") for t in pending],
    )


def _handle_log_exception(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    note = entities.get("exception_note", "Exception logged via voice")
    sid = entities.get("shipment_id")
    if sid:
        shipment_service.update_status(
            sid,
            ShipmentStatusUpdate(status=ShipmentStatus.EXCEPTION, note=note),
            req.user_id,
        )
    task = task_service.create_exception_task(
        description=note,
        location="Current location",
        assigned_to=req.user_id,
        shipment_id=sid,
    )
    return VoiceCommandResponse(
        intent=VoiceIntent.LOG_EXCEPTION,
        entities=entities,
        spoken_response=f"Exception logged: {note}. Task {task.task_id} created for follow-up.",
        action_taken="exception_logged",
        data=task.model_dump(mode="json"),
    )


def _handle_send_notification(entities: dict, req: VoiceCommandRequest) -> VoiceCommandResponse:
    sid = entities.get("shipment_id")
    msg = "Delay notification sent to the consignee." if sid else "Notification sent."
    return VoiceCommandResponse(
        intent=VoiceIntent.SEND_NOTIFICATION,
        entities=entities,
        spoken_response=msg,
        action_taken="notification_sent",
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    VoiceIntent.TRACK_SHIPMENT: _handle_track,
    VoiceIntent.MARK_PICKED: _handle_mark_picked,
    VoiceIntent.MARK_DELIVERED: _handle_mark_delivered,
    VoiceIntent.NEXT_STOP: _handle_next_stop,
    VoiceIntent.LIST_TASKS: _handle_list_tasks,
    VoiceIntent.LOG_EXCEPTION: _handle_log_exception,
    VoiceIntent.SEND_NOTIFICATION: _handle_send_notification,
    VoiceIntent.UPDATE_STATUS: _handle_track,  # fallback to track for generic update
}


def process_voice_command(req: VoiceCommandRequest) -> VoiceCommandResponse:
    intent, entities = classify_intent(req.text)
    handler = _HANDLERS.get(intent)
    if handler:
        return handler(entities, req)
    return VoiceCommandResponse(
        intent=VoiceIntent.UNKNOWN,
        entities=entities,
        spoken_response=(
            "I didn't understand that command. You can ask me to track a shipment, "
            "check your next stop, list your tasks, or mark a delivery as complete."
        ),
    )
