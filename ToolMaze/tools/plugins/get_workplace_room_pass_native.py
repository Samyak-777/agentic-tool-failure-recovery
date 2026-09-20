"""
get_workplace_room_pass_native Tool Plugin

Function: Retrieve a Workplace-native room reservation pass
Category: Source
Domain: Office
"""

TOOL_NAME = "get_workplace_room_pass_native"

from tools.plugins import get_meeting_rooms_workplace as gmrw


def execute(arguments, context) -> dict:
    room_data = gmrw.execute(arguments, context)
    if "error" in room_data:
        return room_data

    rooms = room_data.get("rooms") or []
    room = rooms[0] if rooms else {"name": "Meeting Room 1", "capacity": 20}
    filters = room_data.get("filters_applied") or {}
    room_name = room.get("name") or "Meeting Room 1"
    return {
        "room_pass_ref": f"wp_{room_name.lower().replace(' ', '_')}",
        "resource_label": room_name,
        "max_people": room.get("capacity", 20),
        "reserve_date": filters.get("date") or arguments.get("date") or "2026-01-16",
        "slot_begin": filters.get("start_time") or arguments.get("start_time") or "09:00",
        "room_name": room_name,
    }
