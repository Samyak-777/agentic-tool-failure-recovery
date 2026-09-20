"""
archive_quote_snapshot_native Tool Plugin

Function: Archive a direct-quote snapshot using a text-first quote-board strategy
Category: Action
Domain: Financial
"""

TOOL_NAME = "archive_quote_snapshot_native"

from tools.plugins import create_document_and_alert as cdaa


def execute(arguments, context) -> dict:
    quote_snapshot = arguments.get("quote_snapshot") or {}
    if not isinstance(quote_snapshot, dict):
        return {"error": "quote_snapshot must be an object"}

    symbol = quote_snapshot.get("symbol") or "UNKNOWN"
    usd_last = quote_snapshot.get("usd_last", 0.0)
    venue = quote_snapshot.get("venue") or "unknown"
    quoted_at = quote_snapshot.get("quoted_at") or "unknown"

    result = cdaa.execute(
        {
            "title": arguments.get("title") or "Quote Snapshot",
            "content": f"{symbol} last={usd_last} USD @ {venue} ({quoted_at})",
            "tags": ["quote", "snapshot", "native"],
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
        "strategy": "direct_quote_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "target_user": result.get("user_id"),
        "instrument": symbol,
    }
