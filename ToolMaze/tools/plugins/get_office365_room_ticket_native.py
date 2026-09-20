"""
get_office365_room_ticket_native Tool Plugin

Function: Retrieve an Office365-native room booking ticket
Category: Source
Domain: Office
"""

TOOL_NAME = "get_office365_room_ticket_native"

from tools.plugins import get_meeting_rooms_office365 as gmro


def execute(arguments, context) -> dict:
    room_data = gmro.execute(arguments, context)
    if "error" in room_data:
        return room_data

    rooms = room_data.get("rooms") or []
    room = rooms[0] if rooms else {"name": "Meeting Room 1", "capacity": 20}
    filters = room_data.get("filters_applied") or {}
    room_name = room.get("name") or "Meeting Room 1"
    return {
        "room_ticket_id": f"o365_{room_name.lower().replace(' ', '_')}",
        "room_name_token": room_name.lower().replace(" ", "_"),
        "seat_limit": room.get("capacity", 20),
        "booking_day": filters.get("date") or arguments.get("date") or "2026-01-16",
        "slot_start": filters.get("start_time") or arguments.get("start_time") or "09:00",
        "room_name": room_name,
    }
