"""
archive_alpha_market_window_native Tool Plugin

Function: Archive an Alpha-native market window
Category: Action
Domain: Financial
"""

TOOL_NAME = "archive_alpha_market_window_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    market_window = arguments.get("market_window") or {}
    if not isinstance(market_window, dict):
        return {"error": "market_window must be an object"}

    result = cdaafd.execute(
        {
            "data": market_window,
            "title": arguments.get("title") or "Market Window",
            "tags": ["market", "alpha", "native"],
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
        "strategy": "alpha_market_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "market_ref": market_window.get("alpha_window_id") or "alpha_market_window",
    }
