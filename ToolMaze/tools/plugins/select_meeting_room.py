"""
select_meeting_room Tool Plugin

Function: Choose the best room from available candidates
Category: Processor
Domain: Office
"""

TOOL_NAME = "select_meeting_room"


def execute(arguments, context) -> dict:
    """选择最合适的会议室"""
    rooms = arguments.get("rooms") or []
    attendees = arguments.get("attendees")

    if not isinstance(rooms, list) or not rooms:
        return {"error": "rooms must be a non-empty list"}

    try:
        attendees = int(attendees)
    except (TypeError, ValueError):
        return {"error": "attendees must be an integer"}

    candidates = []
    for room in rooms:
        if not isinstance(room, dict):
            continue
        name = room.get("name")
        capacity = room.get("capacity")
        if not name:
            continue
        try:
            capacity = int(capacity)
        except (TypeError, ValueError):
            continue
        if capacity >= attendees:
            candidates.append({
                "name": name,
                "capacity": capacity,
                "equipment": room.get("equipment", [])
            })

    if not candidates:
        return {"error": f"No available room can fit {attendees} attendees"}

    candidates.sort(key=lambda room: (room["capacity"], room["name"]))
    chosen = candidates[0]

    return {
        "room_name": chosen["name"],
        "capacity": chosen["capacity"],
        "equipment": chosen.get("equipment", []),
        "selection_reason": f"Smallest available room that fits {attendees} attendees"
    }
