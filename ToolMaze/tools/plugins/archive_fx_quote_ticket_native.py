"""
archive_fx_quote_ticket_native Tool Plugin

Function: Archive an FX-adjusted quote ticket using a structured settlement strategy
Category: Action
Domain: Financial
"""

TOOL_NAME = "archive_fx_quote_ticket_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    quote_ticket = arguments.get("quote_ticket") or {}
    if not isinstance(quote_ticket, dict):
        return {"error": "quote_ticket must be an object"}

    instrument = quote_ticket.get("ticker_code") or "UNKNOWN"
    result = cdaafd.execute(
        {
            "data": quote_ticket,
            "title": arguments.get("title") or "Quote Ticket",
            "tags": ["quote", "fx", "native"],
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
        "strategy": "fx_quote_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "target_user": result.get("user_id"),
        "instrument": instrument,
    }
