"""
archive_utc_moment_card_native Tool Plugin

Function: Archive a UTC-style native time moment card
Category: Action
Domain: General
"""

TOOL_NAME = "archive_utc_moment_card_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    moment_card = arguments.get("moment_card") or {}
    if not isinstance(moment_card, dict):
        return {"error": "moment_card must be an object"}

    result = cdaafd.execute(
        {
            "data": moment_card,
            "title": arguments.get("title") or "Time Moment",
            "tags": ["time", "utc", "native"],
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "archived",
        "strategy": "utc_moment_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "time_ref": moment_card.get("moment_card_id") or "utc_moment",
    }
