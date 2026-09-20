"""
schedule_meeting_with_reminder Tool Plugin

Function: Schedule a meeting and create a reminder
Category: Action
Domain: Office
"""

TOOL_NAME = "schedule_meeting_with_reminder"

CONSTRAINTS = {
    "priority": ["low", "medium", "high"],
}

from tools.plugins import schedule_meeting as sm
from tools.plugins import create_reminder as cr


def execute(arguments, context) -> dict:
    """Schedule a meeting and create a reminder for it."""
    start_time = arguments.get("start_time")
    if not start_time:
        return {"error": "start_time is required"}

    title = arguments.get("title") or "Meeting_01"
    participants = arguments.get("participants") or ["alice@company.com"]
    end_time = arguments.get("end_time") or ""
    description = arguments.get("description") or ""
    priority = arguments.get("priority") or "medium"

    meeting_result = sm.execute(
        {
            "start_time": start_time,
            "title": title,
            "participants": participants,
            "end_time": end_time,
        },
        context,
    )
    if "error" in meeting_result:
        return meeting_result

    reminder_result = cr.execute(
        {
            "datetime": meeting_result.get("start_time"),
            "title": meeting_result.get("title", title),
            "description": description,
            "priority": priority,
        },
        context,
    )
    if "error" in reminder_result:
        return reminder_result

    reminder_result["meeting_id"] = meeting_result.get("meeting_id")
    reminder_result["participants"] = meeting_result.get("participants")
    reminder_result["participant_count"] = meeting_result.get("participant_count")
    reminder_result["meeting_start_time"] = meeting_result.get("start_time")
    reminder_result["meeting_end_time"] = meeting_result.get("end_time")
    reminder_result["invitation_status"] = meeting_result.get("invitation_status")
    return reminder_result
