"""
build_shortlist_reservation_request Tool Plugin

Function: Build a shortlist-based room reservation request
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_shortlist_reservation_request"


def execute(arguments, context) -> dict:
    del context

    shortlist_data = arguments.get("shortlist_data")
    if not isinstance(shortlist_data, dict):
        return {"error": "shortlist_data must be an object"}

    room_name = shortlist_data.get("room_name")
    if not room_name:
        return {"error": "shortlist_data.room_name is required"}

    date = arguments.get("date")
    start_time = arguments.get("start_time")
    end_time = arguments.get("end_time")
    attendees = arguments.get("attendees")

    if not date or not start_time or not end_time:
        return {"error": "date, start_time, and end_time are required"}
    if attendees is None:
        return {"error": "attendees is required"}

    return {
        "room_name": room_name,
        "selection_reason": shortlist_data.get("selection_reason", ""),
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
    }
