"""
reserve_best_shortlisted_room Tool Plugin

Function: Shortlist a meeting room and reserve it in one step
Category: Action
Domain: Office
"""

TOOL_NAME = "reserve_best_shortlisted_room"

from tools.plugins import build_shortlist_reservation_request as bsrr
from tools.plugins import get_meeting_rooms as gmr
from tools.plugins import reserve_shortlisted_room as rsr
from tools.plugins import shortlist_meeting_rooms as smr


def execute(arguments, context) -> dict:
    attendees = arguments.get("attendees")
    date = arguments.get("date")
    start_time = arguments.get("start_time")
    end_time = arguments.get("end_time")

    room_data = gmr.execute(
        {
            "min_capacity": attendees,
            "date": date,
            "start_time": start_time,
        },
        context,
    )
    if "error" in room_data:
        return room_data

    shortlist_data = smr.execute(
        {
            "rooms": room_data.get("rooms", []),
            "attendees": attendees,
        },
        context,
    )
    if "error" in shortlist_data:
        return shortlist_data

    reservation_request = bsrr.execute(
        {
            "shortlist_data": shortlist_data,
            "date": date,
            "start_time": start_time,
            "end_time": end_time,
            "attendees": attendees,
        },
        context,
    )
    if "error" in reservation_request:
        return reservation_request

    result = rsr.execute(
        {
            "room_name": reservation_request.get("room_name"),
            "selection_reason": reservation_request.get("selection_reason"),
            "date": reservation_request.get("date"),
            "start_time": reservation_request.get("start_time"),
            "end_time": reservation_request.get("end_time"),
            "attendees": reservation_request.get("attendees"),
        },
        context,
    )
    if "error" in result:
        return result

    result["workflow"] = "shortlist_then_reserve"
    return result
