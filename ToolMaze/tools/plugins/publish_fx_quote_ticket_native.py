"""
publish_fx_quote_ticket_native Tool Plugin

Function: Publish an FX-quote native ticket summary
Category: Action
Domain: Financial
"""

TOOL_NAME = "publish_fx_quote_ticket_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    fx_quote_ticket = arguments.get("fx_quote_ticket") or {}
    if not isinstance(fx_quote_ticket, dict):
        return {"error": "fx_quote_ticket must be an object"}

    ticker = fx_quote_ticket.get("ticker_code") or "AAPL"
    local_last = fx_quote_ticket.get("local_last", 100.0)
    ccy = fx_quote_ticket.get("settlement_ccy") or "USD"
    fx_rate = fx_quote_ticket.get("fx_rate", 1.0)
    message = f"{ticker}: {local_last} {ccy} (fx {fx_rate})"
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
        "strategy": "fx_quote_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "instrument_ref": fx_quote_ticket.get("ticket_ref") or "fx_quote_ticket",
        "content": result.get("content", message),
    }
