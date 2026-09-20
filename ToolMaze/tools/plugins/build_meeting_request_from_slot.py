"""
build_meeting_request_from_slot Tool Plugin

Function: Build a normalized meeting request from availability data and an extracted slot
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_meeting_request_from_slot"


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
    availability_data = arguments.get("availability_data")
    slot_data = arguments.get("slot_data")

    if not isinstance(contact_data, dict):
        return {"error": "contact_data must be an object"}
    if not isinstance(availability_data, dict):
        return {"error": "availability_data must be an object"}
    if not isinstance(slot_data, dict):
        return {"error": "slot_data must be an object"}

    email = contact_data.get("email")
    if not email:
        return {"error": "contact_data.email is required"}

    query_date = availability_data.get("query_date") or ""
    start_value = slot_data.get("extracted_value") or slot_data.get("start_time") or ""

    end_time = arguments.get("end_time") or ""
    if not end_time:
        for slot in availability_data.get("free_slots") or []:
            if isinstance(slot, dict) and slot.get("start_time") == start_value:
                end_time = slot.get("end_time") or ""
                break

    return {
        "participants": [email],
        "start_time": _compose_datetime(query_date, start_value),
        "end_time": _compose_datetime(query_date, end_time),
        "title": arguments.get("title") or "Meeting",
    }
