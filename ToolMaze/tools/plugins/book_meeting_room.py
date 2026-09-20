"""
book_meeting_room Tool Plugin

Function: Book a meeting room (simulated)
Category: Action
Domain: Office
"""

TOOL_NAME = "book_meeting_room"

CONSTRAINTS = {
    "room_name": ["Conference Room A", "Conference Room B", "Meeting Room 1", "Meeting Room 2"]
}

# Deterministic room availability (increased capacity for flexibility)
ROOMS = {
    "Conference Room A": {"capacity": 50, "equipment": ["Projector", "Whiteboard"]},
    "Conference Room B": {"capacity": 100, "equipment": ["TV Screen", "Video Conference"]},
    "Meeting Room 1": {"capacity": 20, "equipment": ["Whiteboard"]},
    "Meeting Room 2": {"capacity": 30, "equipment": ["Projector"]},
}


def execute(arguments, context) -> dict:
    """
    Book a meeting room (simulation)

    Args:
        arguments: Tool parameters
            - room_name (str): Meeting room name
            - date (str): Booking date (YYYY-MM-DD)
            - start_time (str): Start time (HH:MM)
            - end_time (str): End time (HH:MM)
            - attendees (int, optional): Number of attendees

    Returns:
        dict: Dictionary containing booking status
    """
    # Get room_name (required parameter)
    room_name = arguments.get("room_name")
    if not room_name:
        return {
            "error": "Room name is required"
        }

    # Get date (optional parameter)
    date = arguments.get("date")

    # Get start_time (optional parameter)
    start_time = arguments.get("start_time")

    # Get end_time (optional parameter)
    end_time = arguments.get("end_time")

    # Get attendees (optional parameter with reasonable default)
    attendees = arguments.get("attendees") or 10

    if room_name not in ROOMS:
        return {
            "error": f"Room '{room_name}' not found. Available rooms: {', '.join(ROOMS.keys())}"
        }

    room_info = ROOMS[room_name]

    # Check capacity
    if attendees > room_info["capacity"]:
        return {
            "error": f"Room capacity ({room_info['capacity']}) exceeded. Requested: {attendees}"
        }

    booking_id = "BK168D3"

    return {
        "message": "Meeting room booked successfully",
        "booking_id": booking_id,
        "room_name": room_name,
        "date": date,
        "start_time": start_time,
        "end_time": end_time,
        "attendees": attendees,
        "capacity": room_info["capacity"],
        "equipment": room_info["equipment"]
    }
