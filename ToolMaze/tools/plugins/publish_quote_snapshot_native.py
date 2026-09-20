"""
publish_quote_snapshot_native Tool Plugin

Function: Publish a direct-quote native snapshot summary
Category: Action
Domain: Financial
"""

TOOL_NAME = "publish_quote_snapshot_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    quote_snapshot = arguments.get("quote_snapshot") or {}
    if not isinstance(quote_snapshot, dict):
        return {"error": "quote_snapshot must be an object"}

    symbol = quote_snapshot.get("symbol") or "AAPL"
    usd_last = quote_snapshot.get("usd_last", 100.0)
    venue = quote_snapshot.get("venue") or "quote_board"
    message = f"{symbol}: {usd_last} USD @ {venue}"
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
        "strategy": "direct_quote_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "instrument_ref": quote_snapshot.get("snapshot_ref") or "quote_snapshot",
        "content": result.get("content", message),
    }
