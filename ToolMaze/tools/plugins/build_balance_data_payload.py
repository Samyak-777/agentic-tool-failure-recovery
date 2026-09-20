"""
build_balance_data_payload Tool Plugin

Function: Build a structured balance report payload from account balance and FX data
Category: Processor
Domain: Financial
"""

TOOL_NAME = "build_balance_data_payload"


def execute(arguments, context) -> dict:
    del context

    balance_data = arguments.get("balance_data")
    rate_data = arguments.get("rate_data")
    target_currency = arguments.get("target_currency")

    if not isinstance(balance_data, dict):
        return {"error": "balance_data must be an object"}
    if not isinstance(rate_data, dict):
        return {"error": "rate_data must be an object"}
    if not target_currency:
        return {"error": "target_currency is required"}

    balance = balance_data.get("balance")
    rate = rate_data.get("rate")
    if balance is None or rate is None:
        return {"error": "balance_data.balance and rate_data.rate are required"}

    converted_balance = round(float(balance) * float(rate), 2)
    source_currency = balance_data.get("currency", "USD")

    return {
        "data": {
            "user_id": balance_data.get("user_id"),
            "account_type": balance_data.get("account_type"),
            "balance": balance,
            "source_currency": source_currency,
            "rate": rate,
            "target_currency": target_currency,
            "converted_balance": converted_balance,
        },
        "title": arguments.get("title") or "Balance Report",
        "tags": ["balance", target_currency.lower(), "structured"],
        "user_id": arguments.get("user_id") or balance_data.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
