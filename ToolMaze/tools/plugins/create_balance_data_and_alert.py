"""
create_balance_data_and_alert Tool Plugin

Function: Fetch account balance, build a structured payload, and notify the user
Category: Action
Domain: Financial
"""

TOOL_NAME = "create_balance_data_and_alert"

from tools.plugins import build_balance_data_payload as bbdp
from tools.plugins import create_document_and_alert_from_data as cdaafd
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

    payload = bbdp.execute(
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

    result = cdaafd.execute(
        {
            "data": payload.get("data"),
            "title": payload.get("title"),
            "tags": payload.get("tags"),
            "user_id": payload.get("user_id"),
            "priority": payload.get("priority"),
            "channel": payload.get("channel"),
        },
        context,
    )
    if "error" in result:
        return result

    result["account_type"] = balance_data.get("account_type")
    result["target_currency"] = target_currency
    result["workflow"] = "balance_structured_report"
    return result
