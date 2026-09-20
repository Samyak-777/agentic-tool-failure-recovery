"""
publish_polygon_market_board_native Tool Plugin

Function: Publish a market notice using a Polygon-native market board
Category: Action
Domain: Financial
"""

TOOL_NAME = "publish_polygon_market_board_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    market_board = arguments.get("market_board") or {}
    if not isinstance(market_board, dict):
        return {"error": "market_board must be an object"}

    venue = market_board.get("market_code") or "NYSE"
    phase = market_board.get("session_band") or "unknown"
    transition = market_board.get("next_mark") or "N/A"
    message = f"{venue} band {phase}, next mark {transition}"
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
        "strategy": "polygon_market_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "market_ref": market_board.get("polygon_board_id") or "polygon_market",
        "content": result.get("content", message),
    }
