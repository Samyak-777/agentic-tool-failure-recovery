"""
archive_directory_contact_card_native Tool Plugin

Function: Archive a directory-native contact card
Category: Action
Domain: Office
"""

TOOL_NAME = "archive_directory_contact_card_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    contact_card = arguments.get("contact_card") or {}
    if not isinstance(contact_card, dict):
        return {"error": "contact_card must be an object"}

    result = cdaafd.execute(
        {
            "data": contact_card,
            "title": arguments.get("title") or "Directory Contact Card",
            "tags": ["contact", "directory", "native"],
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
        "strategy": "directory_contact_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "contact_ref": contact_card.get("card_id") or "dir_contact_card",
    }
