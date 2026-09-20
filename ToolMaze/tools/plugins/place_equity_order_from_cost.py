"""
place_equity_order_from_cost Tool Plugin
Category: Action
Domain: Financial
"""

TOOL_NAME = "place_equity_order_from_cost"

from tools.plugins import place_buy_order_with_risk_check as pbor


def execute(arguments, context) -> dict:
    result = pbor.execute(
        {
            "amount": arguments.get("amount"),
        },
        context,
    )
    if "error" in result:
        return result

    result["ticker"] = (arguments.get("ticker") or "").upper()
    result["order_strategy"] = "equity_cost_checked"
    return result
