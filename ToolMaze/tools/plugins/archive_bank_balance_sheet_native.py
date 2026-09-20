"""
archive_bank_balance_sheet_native Tool Plugin

Function: Archive a bank-native balance sheet snapshot
Category: Action
Domain: Financial
"""

TOOL_NAME = "archive_bank_balance_sheet_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    balance_sheet = arguments.get("balance_sheet") or {}
    if not isinstance(balance_sheet, dict):
        return {"error": "balance_sheet must be an object"}

    result = cdaafd.execute(
        {
            "data": balance_sheet,
            "title": arguments.get("title") or "Balance Sheet",
            "tags": ["balance", "bank", "native"],
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
        "strategy": "bank_balance_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "account_ref": balance_sheet.get("sheet_id") or "bank_sheet",
    }
