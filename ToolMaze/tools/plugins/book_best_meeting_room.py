"""
book_best_meeting_room Tool Plugin

Function: Automatically choose and book the best available meeting room
Category: Action
Domain: Office
"""

TOOL_NAME = "book_best_meeting_room"

from tools.plugins import get_meeting_rooms as gmr
from tools.plugins import select_meeting_room as smr
from tools.plugins import book_meeting_room as bmr


def execute(arguments, context) -> dict:
    """自动选择并预订最合适的会议室"""
    attendees = arguments.get("attendees")
    if attendees is None:
        return {"error": "attendees is required"}

    date = arguments.get("date") or "2026-01-15"
    start_time = arguments.get("start_time") or "14:00"
    end_time = arguments.get("end_time") or "15:00"

    rooms_result = gmr.execute(
        {
            "min_capacity": attendees,
            "date": date,
            "start_time": start_time,
        },
        context,
    )
    if "error" in rooms_result:
        return rooms_result

    selection = smr.execute(
        {
            "rooms": rooms_result.get("rooms", []),
            "attendees": attendees,
        },
        context,
    )
    if "error" in selection:
        return selection

    booking = bmr.execute(
        {
            "room_name": selection["room_name"],
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees,
        },
        context,
    )
    if "error" in booking:
        return booking

    booking["selection_reason"] = selection.get("selection_reason")
    return booking
