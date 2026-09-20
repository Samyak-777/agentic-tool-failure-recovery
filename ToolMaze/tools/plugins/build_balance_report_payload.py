"""
build_balance_report_payload Tool Plugin

Function: Fetch account balance, convert currency, and build a text balance report payload
Category: Processor
Domain: Financial
"""

TOOL_NAME = "build_balance_report_payload"

from tools.plugins import build_balance_text_report as bbtr
from tools.plugins import get_account_balance_bank_api as gabb
from tools.plugins import get_exchange_rate_fixer as gerf


def execute(arguments, context) -> dict:
    balance_data = gabb.execute(
        {
            "user_id": arguments.get("user_id"),
            "account_type": arguments.get("account_type") or "checking",
        },
        context,
    )
    if "error" in balance_data:
        return balance_data

    target_currency = arguments.get("target_currency")
    rate_data = gerf.execute(
        {
            "from_currency": balance_data.get("currency") or "USD",
            "to_currency": target_currency,
        },
        context,
    )
    if "error" in rate_data:
        return rate_data

    payload = bbtr.execute(
        {
            "balance_data": balance_data,
            "rate_data": rate_data,
            "target_currency": target_currency,
            "title": arguments.get("title") or "Balance Report",
            "user_id": arguments.get("user_id") or balance_data.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in payload:
        return payload

    payload["account_type"] = balance_data.get("account_type")
    payload["target_currency"] = target_currency
    return payload
