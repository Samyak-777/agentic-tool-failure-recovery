"""
query_availability Tool Plugin
Function: Query calendar for available time slots
Category: Source
Domain: Office
"""

TOOL_NAME = "query_availability"

ALTERNATIVE_TOOLS = [
    "query_availability",
    "query_availability_google_calendar",
    "query_availability_outlook_calendar",
    "query_availability_caldav",
]

CONSTRAINTS = {
    "item_id": ["u_alice", "u_bob", "u_charlie", "u_david"]
}

OFFICE_MOCK_DATA = {
    "users": {
        "alice": {"email": "alice@company.com", "id": "u_alice"},
        "bob": {"email": "bob@company.com", "id": "u_bob"},
        "charlie": {"email": "charlie@company.com", "id": "u_charlie"},
        "david": {"email": "david@company.com", "id": "u_david"},
    },
    "calendar": {
        "u_alice": {"2024-10-24": ["09:00", "10:00", "14:00", "15:00"]},
        "u_bob": {"2024-10-24": ["10:00", "11:00", "14:00", "16:00"]},
        "u_charlie": {"2024-10-24": ["09:00", "14:00", "15:00", "16:00"]},
        "u_david": {"2024-10-24": ["09:00", "10:00", "14:00", "16:00"]},
    },
}



def _collect_booked_times(start_date, context):
    booked_times = set()
    if not hasattr(context, "history"):
        return booked_times

    for record in context.history:
        if record.tool_name not in ["schedule_meeting", "book_meeting_room"]:
            continue
        if "error" in record.output:
            continue

        meeting_date = record.output.get("date") or record.arguments.get("date")
        meeting_start = record.output.get("start_time") or record.arguments.get("start_time")
        if meeting_date != start_date or not meeting_start:
            continue

        if " " in meeting_start:
            meeting_start = meeting_start.split(" ", 1)[1]
        booked_times.add(meeting_start)

    return booked_times



def _build_availability_result(item_id, start_date, context):
    user_calendar = OFFICE_MOCK_DATA["calendar"].get(item_id)
    if not user_calendar:
        return {"error": f"User calendar not found for {item_id}"}

    slots = user_calendar.get(start_date, [])
    booked_times = _collect_booked_times(start_date, context)

    formatted_slots = []
    for start_time in slots:
        if start_time in booked_times:
            continue

        hour = int(start_time.split(":")[0])
        formatted_slots.append(
            {
                "date": start_date,
                "start_time": start_time,
                "end_time": f"{hour + 1:02d}:00",
                "status": "free",
            }
        )

    return {
        "user_id": item_id,
        "query_date": start_date,
        "free_slots": formatted_slots,
        "total_slots": len(formatted_slots),
    }



def execute(arguments, context) -> dict:
    item_id = arguments.get("item_id")
    if not item_id:
        return {"error": "item_id is required"}

    raw_start_date = arguments.get("start_date")
    if hasattr(context, "find_alternative_output"):
        args_match = {"item_id": item_id}
        if raw_start_date is not None:
            args_match["start_date"] = raw_start_date
        existing = context.find_alternative_output(ALTERNATIVE_TOOLS, args_match)
        if existing:
            return existing

    start_date = raw_start_date or "2024-10-24"
    return _build_availability_result(item_id, start_date, context)
