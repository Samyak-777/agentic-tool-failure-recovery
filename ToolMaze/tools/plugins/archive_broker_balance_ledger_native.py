"""
archive_broker_balance_ledger_native Tool Plugin

Function: Archive a broker-native balance ledger snapshot
Category: Action
Domain: Financial
"""

TOOL_NAME = "archive_broker_balance_ledger_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    balance_ledger = arguments.get("balance_ledger") or {}
    if not isinstance(balance_ledger, dict):
        return {"error": "balance_ledger must be an object"}

    result = cdaafd.execute(
        {
            "data": balance_ledger,
            "title": arguments.get("title") or "Balance Ledger",
            "tags": ["balance", "broker", "native"],
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
        "strategy": "broker_balance_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "account_ref": balance_ledger.get("ledger_ref") or "broker_ledger",
    }
