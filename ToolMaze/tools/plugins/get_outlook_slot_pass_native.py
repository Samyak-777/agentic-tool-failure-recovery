"""
get_outlook_slot_pass_native Tool Plugin

Function: Retrieve an Outlook-native slot pass
Category: Source
Domain: Office
"""

TOOL_NAME = "get_outlook_slot_pass_native"

from tools.plugins import query_availability_outlook_calendar as qaoc


def execute(arguments, context) -> dict:
    availability = qaoc.execute(arguments, context)
    if "error" in availability:
        return availability

    slots = availability.get("free_slots") or []
    slot = slots[0] if slots else {}
    item_id = availability.get("user_id") or arguments.get("item_id") or "u_alice"
    start_date = slot.get("date") or availability.get("query_date") or arguments.get("start_date") or "2024-10-24"
    return {
        "slot_pass_ref": f"oslot_{item_id}_{start_date}",
        "attendee_id": item_id,
        "slot_day": start_date,
        "window_begin": slot.get("start_time") or "09:00",
        "window_end": slot.get("end_time") or "10:00",
        "provider_label": "outlook_calendar",
    }
