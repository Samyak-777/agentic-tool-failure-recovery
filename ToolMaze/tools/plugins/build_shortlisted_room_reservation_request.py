"""
build_shortlisted_room_reservation_request Tool Plugin

Function: Search meeting rooms, shortlist the best room, and build a reservation request
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_shortlisted_room_reservation_request"

from tools.plugins import build_shortlist_reservation_request as bsrr
from tools.plugins import get_meeting_rooms as gmr
from tools.plugins import shortlist_meeting_rooms as smr


def execute(arguments, context) -> dict:
    room_data = gmr.execute(
        {
            "min_capacity": arguments.get("attendees"),
            "date": arguments.get("date"),
            "start_time": arguments.get("start_time"),
        },
        context,
    )
    if "error" in room_data:
        return room_data

    shortlist_data = smr.execute(
        {
            "rooms": room_data.get("rooms", []),
            "attendees": arguments.get("attendees"),
        },
        context,
    )
    if "error" in shortlist_data:
        return shortlist_data

    request = bsrr.execute(
        {
            "shortlist_data": shortlist_data,
            "date": arguments.get("date"),
            "start_time": arguments.get("start_time"),
            "end_time": arguments.get("end_time"),
            "attendees": arguments.get("attendees"),
        },
        context,
    )
    if "error" in request:
        return request

    return request
