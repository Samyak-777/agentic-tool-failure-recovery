"""
get_meeting_rooms Tool Plugin

Function: List available meeting rooms
Category: Source
Domain: Office
"""

TOOL_NAME = "get_meeting_rooms"

ALTERNATIVE_TOOLS = [
    "get_meeting_rooms",
    "get_meeting_rooms_office365",
    "get_meeting_rooms_workplace",
    "get_meeting_rooms_google_workspace",
]

ROOMS = {
    "Conference Room A": {"capacity": 50, "equipment": ["Projector", "Whiteboard"]},
    "Conference Room B": {"capacity": 100, "equipment": ["TV Screen", "Video Conference"]},
    "Meeting Room 1": {"capacity": 20, "equipment": ["Whiteboard"]},
    "Meeting Room 2": {"capacity": 30, "equipment": ["Projector"]},
}



def _collect_booked_rooms(date, start_time, context):
    booked_rooms = set()
    if not date or not start_time or not hasattr(context, "history"):
        return booked_rooms

    for record in context.history:
        if record.tool_name != "book_meeting_room" or "error" in record.output:
            continue

        booked_date = record.output.get("date")
        booked_start = record.output.get("start_time")
        booked_room = record.output.get("room_name")
        if booked_date == date and booked_start == start_time and booked_room:
            booked_rooms.add(booked_room)

    return booked_rooms



def _build_rooms_result(min_capacity, date, start_time, context):
    booked_rooms = _collect_booked_rooms(date, start_time, context)
    available_rooms = []

    for name, details in ROOMS.items():
        if name in booked_rooms:
            continue
        if details["capacity"] < min_capacity:
            continue

        available_rooms.append(
            {
                "name": name,
                "capacity": details["capacity"],
                "equipment": details["equipment"],
            }
        )

    available_rooms.sort(key=lambda room: (room["capacity"], room["name"]))
    return {
        "count": len(available_rooms),
        "rooms": available_rooms,
        "filters_applied": {
            "min_capacity": min_capacity,
            "date": date,
            "start_time": start_time,
        },
    }



def execute(arguments, context) -> dict:
    raw_min_capacity = arguments.get("min_capacity")
    raw_date = arguments.get("date")
    raw_start_time = arguments.get("start_time")

    if hasattr(context, "find_alternative_output"):
        args_match = {}
        if raw_min_capacity is not None:
            args_match["min_capacity"] = raw_min_capacity
        if raw_date is not None:
            args_match["date"] = raw_date
        if raw_start_time is not None:
            args_match["start_time"] = raw_start_time
        if args_match:
            existing = context.find_alternative_output(ALTERNATIVE_TOOLS, args_match)
            if existing:
                return existing

    min_capacity = raw_min_capacity or 0
    return _build_rooms_result(min_capacity, raw_date, raw_start_time, context)
