"""
archive_booking_stay_sheet_native Tool Plugin

Function: Archive a Booking-native stay sheet
Category: Action
Domain: Travel
"""

TOOL_NAME = "archive_booking_stay_sheet_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    stay_sheet = arguments.get("stay_sheet") or {}
    if not isinstance(stay_sheet, dict):
        return {"error": "stay_sheet must be an object"}

    result = cdaafd.execute(
        {
            "data": stay_sheet,
            "title": arguments.get("title") or "Stay Sheet",
            "tags": ["hotel", "booking", "native"],
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
        "strategy": "booking_stay_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "property_ref": stay_sheet.get("stay_sheet_id") or "booking_stay",
    }
