"""
place_sell_order_from_converted_quote Tool Plugin

Function: Place a sell order from a normalized converted-quote sell request
Category: Action
Domain: Financial
"""

TOOL_NAME = "place_sell_order_from_converted_quote"

from tools.plugins import place_sell_order as pso


def execute(arguments, context) -> dict:
    ticker = arguments.get("ticker")
    quantity = arguments.get("quantity")
    price_usd = arguments.get("price_usd")

    if not ticker:
        return {"error": "ticker is required"}
    if quantity is None:
        return {"error": "quantity is required"}
    if price_usd is None:
        return {"error": "price_usd is required"}

    result = pso.execute(
        {
            "ticker": ticker,
            "quantity": quantity,
            "price": price_usd,
        },
        context,
    )
    if "error" in result:
        return result

    result["price_usd"] = price_usd
    result["converted_price"] = arguments.get("converted_price", 0)
    result["target_currency"] = arguments.get("target_currency", "USD")
    return result
