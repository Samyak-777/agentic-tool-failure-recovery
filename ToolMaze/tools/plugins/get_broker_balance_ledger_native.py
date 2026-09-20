"""
get_broker_balance_ledger_native Tool Plugin

Function: Retrieve a broker-native balance ledger snapshot
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_broker_balance_ledger_native"

from tools.plugins import get_account_balance_broker_api as gabr


def execute(arguments, context) -> dict:
    balance = gabr.execute(arguments, context)
    if "error" in balance:
        return balance

    account_type = balance.get("account_type") or arguments.get("account_type") or "investment"
    user_id = balance.get("user_id") or arguments.get("user_id") or "default_user"
    return {
        "ledger_ref": f"broker_{user_id}_{account_type}",
        "principal_id": user_id,
        "equity_value": balance.get("balance", 0),
        "currency_code": balance.get("currency", "USD"),
        "account_bucket": account_type,
    }
