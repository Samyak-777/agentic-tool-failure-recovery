"""
publish_alpha_market_window_native Tool Plugin

Function: Publish a market notice using an Alpha-native market window
Category: Action
Domain: Financial
"""

TOOL_NAME = "publish_alpha_market_window_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    market_window = arguments.get("market_window") or {}
    if not isinstance(market_window, dict):
        return {"error": "market_window must be an object"}

    venue = market_window.get("venue_code") or "NYSE"
    phase = market_window.get("phase_label") or "unknown"
    transition = market_window.get("transition_mark") or "N/A"
    message = f"{venue} session {phase}, next transition {transition}"
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
        "strategy": "alpha_market_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "market_ref": market_window.get("alpha_window_id") or "alpha_market",
        "content": result.get("content", message),
    }
