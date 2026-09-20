"""
archive_gnews_digest_cards_native Tool Plugin

Function: Archive a GNews-native digest card bundle
Category: Action
Domain: General
"""

TOOL_NAME = "archive_gnews_digest_cards_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    digest_cards = arguments.get("digest_cards") or {}
    if not isinstance(digest_cards, dict):
        return {"error": "digest_cards must be an object"}

    topic = digest_cards.get("topic") or "general"
    result = cdaafd.execute(
        {
            "data": digest_cards,
            "title": arguments.get("title") or "News Digest",
            "tags": ["news", "digest", "native"],
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
        "strategy": "gnews_digest_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "topic": topic,
    }
