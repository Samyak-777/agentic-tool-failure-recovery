"""
place_sell_order_from_quote Tool Plugin

Function: Place a sell order from a normalized quote-derived sell request
Category: Action
Domain: Financial
"""

TOOL_NAME = "place_sell_order_from_quote"

from tools.plugins import place_sell_order as pso


def execute(arguments, context) -> dict:
    ticker = arguments.get("ticker")
    quantity = arguments.get("quantity")
    price = arguments.get("price")

    if not ticker:
        return {"error": "ticker is required"}
    if quantity is None:
        return {"error": "quantity is required"}
    if price is None:
        return {"error": "price is required"}

    result = pso.execute(
        {
            "ticker": ticker,
            "quantity": quantity,
            "price": price,
        },
        context,
    )
    if "error" in result:
        return result

    result["price"] = price
    return result
