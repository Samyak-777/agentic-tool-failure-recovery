"""
get_google_slot_ticket_native Tool Plugin

Function: Retrieve a Google Calendar-native slot ticket
Category: Source
Domain: Office
"""

TOOL_NAME = "get_google_slot_ticket_native"

from tools.plugins import query_availability_google_calendar as qagc


def execute(arguments, context) -> dict:
    availability = qagc.execute(arguments, context)
    if "error" in availability:
        return availability

    slots = availability.get("free_slots") or []
    slot = slots[0] if slots else {}
    item_id = availability.get("user_id") or arguments.get("item_id") or "u_alice"
    start_date = slot.get("date") or availability.get("query_date") or arguments.get("start_date") or "2024-10-24"
    return {
        "slot_ticket_id": f"gslot_{item_id}_{start_date}",
        "owner_user_id": item_id,
        "slot_date": start_date,
        "slot_start": slot.get("start_time") or "09:00",
        "slot_end": slot.get("end_time") or "10:00",
        "provider_label": "google_calendar",
    }
