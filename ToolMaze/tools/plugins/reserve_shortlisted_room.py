"""
reserve_shortlisted_room Tool Plugin
Category: Action
Domain: Office
"""

TOOL_NAME = "reserve_shortlisted_room"

from tools.plugins import book_meeting_room as bmr


def execute(arguments, context) -> dict:
    result = bmr.execute(
        {
            "room_name": arguments.get("room_name"),
            "date": arguments.get("date"),
            "start_time": arguments.get("start_time"),
            "end_time": arguments.get("end_time"),
            "attendees": arguments.get("attendees"),
        },
        context,
    )
    if "error" in result:
        return result

    result["selection_reason"] = arguments.get("selection_reason") or ""
    result["reservation_strategy"] = "shortlist_then_reserve"
    return result
