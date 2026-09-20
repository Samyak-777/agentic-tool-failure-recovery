"""
publish_bank_balance_sheet_native Tool Plugin

Function: Publish a balance notice using a bank-native balance sheet
Category: Action
Domain: Financial
"""

TOOL_NAME = "publish_bank_balance_sheet_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    balance_sheet = arguments.get("balance_sheet") or {}
    if not isinstance(balance_sheet, dict):
        return {"error": "balance_sheet must be an object"}

    message = (
        f"Bank balance {balance_sheet.get('bucket_name', 'account')}: "
        f"{balance_sheet.get('balance_amount', 0)} {balance_sheet.get('denomination', 'USD')}"
    )
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
        "strategy": "bank_balance_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "account_ref": balance_sheet.get("sheet_id") or "bank_balance_sheet",
        "content": result.get("content", message),
    }
