"""
place_equity_order_from_risk Tool Plugin
Category: Action
Domain: Financial
"""

TOOL_NAME = "place_equity_order_from_risk"

from tools.plugins import place_buy_order as pbo


def execute(arguments, context) -> dict:
    result = pbo.execute(
        {
            "risk_token": arguments.get("risk_token"),
            "price": arguments.get("limit_price"),
        },
        context,
    )
    if "error" in result:
        return result

    result["ticker"] = (arguments.get("ticker") or "").upper()
    result["limit_price"] = arguments.get("limit_price")
    result["order_strategy"] = "equity_risk_review"
    return result
