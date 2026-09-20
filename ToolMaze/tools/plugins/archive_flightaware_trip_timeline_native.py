"""
archive_flightaware_trip_timeline_native Tool Plugin

Function: Archive a FlightAware-native trip timeline
Category: Action
Domain: Travel
"""

TOOL_NAME = "archive_flightaware_trip_timeline_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    trip_timeline = arguments.get("trip_timeline") or {}
    if not isinstance(trip_timeline, dict):
        return {"error": "trip_timeline must be an object"}

    result = cdaafd.execute(
        {
            "data": trip_timeline,
            "title": arguments.get("title") or "Trip Timeline",
            "tags": ["flight", "timeline", "native"],
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
        "strategy": "flightaware_timeline_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "transport_ref": trip_timeline.get("timeline_id") or "trip_timeline",
    }
