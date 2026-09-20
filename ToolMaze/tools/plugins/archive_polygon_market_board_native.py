"""
archive_polygon_market_board_native Tool Plugin

Function: Archive a Polygon-native market board
Category: Action
Domain: Financial
"""

TOOL_NAME = "archive_polygon_market_board_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    market_board = arguments.get("market_board") or {}
    if not isinstance(market_board, dict):
        return {"error": "market_board must be an object"}

    result = cdaafd.execute(
        {
            "data": market_board,
            "title": arguments.get("title") or "Market Board",
            "tags": ["market", "polygon", "native"],
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
        "strategy": "polygon_market_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "market_ref": market_board.get("polygon_board_id") or "polygon_market_board",
    }
