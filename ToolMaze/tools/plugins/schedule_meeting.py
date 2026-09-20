"""
schedule_meeting Tool Plugin

Function: Schedule a meeting and send invitations (simulated)
Category: Action
Domain: Office
"""

TOOL_NAME = "schedule_meeting"


from datetime import datetime, timedelta

def add_one_hour(time_str: str) -> str:
    try:
        base_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError as e:
        return ""
    new_time = base_time + timedelta(hours=1)
    return new_time.strftime("%Y-%m-%d %H:%M")

def execute(arguments, context) -> dict:
    """
    Schedule a meeting and send invitation emails (simulation)

    Args:
        arguments: Tool parameters
            - title (str): Meeting title
            - participants (list): List of participant email addresses
            - start_time (str): Meeting start time (YYYY-MM-DD HH:MM)
            - end_time (str): Meeting end time (YYYY-MM-DD HH:MM)

    Returns:
        dict: Dictionary containing meeting scheduling status
    """
    # Get start_time (required parameter)
    start_time = arguments.get("start_time")
    if not start_time:
        return {
            "error": "Meeting start_time is required"
        }

    # Get title (optional parameter with reasonable default)
    title = arguments.get("title") or "Meeting_01"

    # Get participants (optional parameter with reasonable default)
    participants = arguments.get("participants") or ['alice@company.com']

    # Get end_time (optional parameter)
    end_time = arguments.get("end_time")

    # Auto-calculate end_time if not provided
    if not end_time and start_time:
        end_time = add_one_hour(start_time)

    # Validate participants format
    if not isinstance(participants, list):
        participants = [participants]

    meeting_id = "MTG-5A3B2C1D"

    # Simulate successful scheduling
    return {
        "status": "meeting scheduled",
        "message": "Meeting scheduled successfully and invitations sent",
        "meeting_id": meeting_id,
        "title": title,
        "participants": participants,
        "participant_count": len(participants),
        "start_time": start_time,
        "end_time": end_time,
        "invitation_status": "sent"
    }

