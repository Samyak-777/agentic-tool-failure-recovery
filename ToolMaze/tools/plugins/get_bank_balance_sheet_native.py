"""
get_bank_balance_sheet_native Tool Plugin

Function: Retrieve a bank-native balance sheet snapshot
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_bank_balance_sheet_native"

from tools.plugins import get_account_balance_bank_api as gabb


def execute(arguments, context) -> dict:
    balance = gabb.execute(arguments, context)
    if "error" in balance:
        return balance

    account_type = balance.get("account_type") or arguments.get("account_type") or "checking"
    user_id = balance.get("user_id") or arguments.get("user_id") or "default_user"
    return {
        "sheet_id": f"bank_{user_id}_{account_type}",
        "owner_id": user_id,
        "balance_amount": balance.get("balance", 0),
        "denomination": balance.get("currency", "USD"),
        "bucket_name": account_type,
    }
