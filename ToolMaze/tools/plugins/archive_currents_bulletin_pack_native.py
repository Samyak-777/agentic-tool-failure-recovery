"""
archive_currents_bulletin_pack_native Tool Plugin

Function: Archive a Currents-native bulletin pack
Category: Action
Domain: General
"""

TOOL_NAME = "archive_currents_bulletin_pack_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    bulletin_pack = arguments.get("bulletin_pack") or {}
    if not isinstance(bulletin_pack, dict):
        return {"error": "bulletin_pack must be an object"}

    topic = bulletin_pack.get("vertical") or "general"
    result = cdaafd.execute(
        {
            "data": bulletin_pack,
            "title": arguments.get("title") or "News Bulletin Pack",
            "tags": ["news", "bulletin", "native"],
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
        "strategy": "currents_bulletin_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "topic": topic,
    }
