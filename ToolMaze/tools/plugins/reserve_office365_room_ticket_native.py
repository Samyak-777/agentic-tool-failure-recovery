"""
reserve_office365_room_ticket_native Tool Plugin

Function: Reserve a room using an Office365-native room ticket
Category: Action
Domain: Office
"""

TOOL_NAME = "reserve_office365_room_ticket_native"

from tools.plugins import book_meeting_room as bmr


def execute(arguments, context) -> dict:
    room_ticket = arguments.get("room_ticket") or {}
    if not isinstance(room_ticket, dict):
        return {"error": "room_ticket must be an object"}

    room_name = room_ticket.get("room_name") or "Meeting Room 1"
    date = room_ticket.get("booking_day") or "2026-01-16"
    start_time = room_ticket.get("slot_start") or "09:00"
    attendees = arguments.get("attendees") or min(room_ticket.get("seat_limit", 10), 10)
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
        "strategy": "office365_room_booking_native",
        "booking_id": result.get("booking_id"),
        "resource_ref": room_ticket.get("room_ticket_id") or "o365_room",
        "room_name": result.get("room_name", room_name),
        "date": result.get("date", date),
    }
