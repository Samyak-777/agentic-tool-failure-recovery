"""
reserve_workplace_room_pass_native Tool Plugin

Function: Reserve a room using a Workplace-native room pass
Category: Action
Domain: Office
"""

TOOL_NAME = "reserve_workplace_room_pass_native"

from tools.plugins import book_meeting_room as bmr


def execute(arguments, context) -> dict:
    room_pass = arguments.get("room_pass") or {}
    if not isinstance(room_pass, dict):
        return {"error": "room_pass must be an object"}

    room_name = room_pass.get("room_name") or room_pass.get("resource_label") or "Meeting Room 1"
    date = room_pass.get("reserve_date") or "2026-01-16"
    start_time = room_pass.get("slot_begin") or "09:00"
    attendees = arguments.get("attendees") or min(room_pass.get("max_people", 10), 10)
    end_time = arguments.get("end_time") or "10:00"

    result = bmr.execute(
        {
            "room_name": room_name,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees,
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "reserved",
        "strategy": "workplace_room_booking_native",
        "booking_id": result.get("booking_id"),
        "resource_ref": room_pass.get("room_pass_ref") or "wp_room",
        "room_name": result.get("room_name", room_name),
        "date": result.get("date", date),
    }
