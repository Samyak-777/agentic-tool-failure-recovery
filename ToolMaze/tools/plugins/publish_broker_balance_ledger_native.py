"""
publish_broker_balance_ledger_native Tool Plugin

Function: Publish a balance notice using a broker-native balance ledger
Category: Action
Domain: Financial
"""

TOOL_NAME = "publish_broker_balance_ledger_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    balance_ledger = arguments.get("balance_ledger") or {}
    if not isinstance(balance_ledger, dict):
        return {"error": "balance_ledger must be an object"}

    message = (
        f"Broker balance {balance_ledger.get('account_bucket', 'account')}: "
        f"{balance_ledger.get('equity_value', 0)} {balance_ledger.get('currency_code', 'USD')}"
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
        "strategy": "broker_balance_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "account_ref": balance_ledger.get("ledger_ref") or "broker_balance_ledger",
        "content": result.get("content", message),
    }
