"""
publish_gnews_digest_cards_native Tool Plugin

Function: Publish a news notice using a GNews-native digest card bundle
Category: Action
Domain: General
"""

TOOL_NAME = "publish_gnews_digest_cards_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    digest_cards = arguments.get("digest_cards") or {}
    if not isinstance(digest_cards, dict):
        return {"error": "digest_cards must be an object"}

    cards = digest_cards.get("cards") or []
    headline = cards[0].get("headline") if cards and isinstance(cards[0], dict) else "News update"
    message = f"{digest_cards.get('topic', 'general')}: {headline}"
    user_id = arguments.get("user_id") or "default_user"
    result = pa.execute(
        {
            "message": message,
            "user_id": user_id,
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "published",
        "strategy": "gnews_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "news_ref": digest_cards.get("digest_id") or "gnews_digest_cards",
        "content": result.get("content", message),
    }
