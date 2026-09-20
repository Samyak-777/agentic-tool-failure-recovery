"""
shortlist_meeting_rooms Tool Plugin
Category: Processor
Domain: Office
"""

TOOL_NAME = "shortlist_meeting_rooms"


def execute(arguments, context) -> dict:
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

        if capacity < attendees:
            continue

        equipment = room.get("equipment", [])
        candidates.append({
            "name": name,
            "capacity": capacity,
            "equipment": equipment,
            "equipment_count": len(equipment),
        })

    if not candidates:
        return {"error": f"No available room can fit {attendees} attendees"}

    candidates.sort(key=lambda room: (-room["equipment_count"], room["capacity"], room["name"]))
    chosen = candidates[0]

    return {
        "room_name": chosen["name"],
        "capacity": chosen["capacity"],
        "equipment": chosen["equipment"],
        "selection_reason": (
            f"Most equipped room that still fits {attendees} attendees"
        ),
    }
