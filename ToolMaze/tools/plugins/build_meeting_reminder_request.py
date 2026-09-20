"""
build_meeting_reminder_request Tool Plugin

Function: Build a normalized meeting-with-reminder request from a recommended meeting slot
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_meeting_reminder_request"


def _compose_datetime(date_str, time_str):
    if not time_str:
        return ""
    if isinstance(time_str, str) and " " in time_str:
        return time_str
    if not date_str:
        return str(time_str)
    return f"{date_str} {time_str}"


def execute(arguments, context) -> dict:
    del context

    contact_data = arguments.get("contact_data")
    meeting_slot = arguments.get("meeting_slot")

    if not isinstance(contact_data, dict):
        return {"error": "contact_data must be an object"}
    if not isinstance(meeting_slot, dict):
        return {"error": "meeting_slot must be an object"}

    email = contact_data.get("email")
    if not email:
        return {"error": "contact_data.email is required"}

    recommended_slot = meeting_slot.get("recommended_slot") or {}
    date_str = meeting_slot.get("date") or ""

    return {
        "participants": [email],
        "start_time": _compose_datetime(date_str, recommended_slot.get("start_time")),
        "end_time": _compose_datetime(date_str, recommended_slot.get("end_time")),
        "title": arguments.get("title") or "Meeting",
        "description": arguments.get("description") or "",
        "priority": arguments.get("priority") or "medium",
    }
