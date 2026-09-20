"""
build_balance_text_report Tool Plugin

Function: Build a text-based balance report from account balance and FX data
Category: Processor
Domain: Financial
"""

TOOL_NAME = "build_balance_text_report"


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

    content = "\n".join([
        f"User: {balance_data.get('user_id')}",
        f"Account Type: {balance_data.get('account_type')}",
        f"Balance: {balance} {source_currency}",
        f"FX Rate: 1 {source_currency} = {rate} {target_currency}",
        f"Converted Balance: {converted_balance} {target_currency}",
    ])

    return {
        "title": arguments.get("title") or "Balance Report",
        "content": content,
        "tags": ["balance", target_currency.lower()],
        "user_id": arguments.get("user_id") or balance_data.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
