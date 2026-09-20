"""
build_room_booking_request Tool Plugin

Function: Build a normalized room-booking request from a selected room
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_room_booking_request"


def execute(arguments, context) -> dict:
    del context

    selection_data = arguments.get("selection_data")
    if not isinstance(selection_data, dict):
        return {"error": "selection_data must be an object"}

    room_name = selection_data.get("room_name")
    if not room_name:
        return {"error": "selection_data.room_name is required"}

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
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "selection_reason": selection_data.get("selection_reason", ""),
    }
