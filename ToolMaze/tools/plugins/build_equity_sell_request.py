"""
build_equity_sell_request Tool Plugin

Function: Build a normalized sell-order request from an equity quote
Category: Processor
Domain: Financial
"""

TOOL_NAME = "build_equity_sell_request"


def execute(arguments, context) -> dict:
    del context

    quote_data = arguments.get("quote_data")
    ticker = arguments.get("ticker")
    quantity = arguments.get("quantity")

    if not isinstance(quote_data, dict):
        return {"error": "quote_data must be an object"}
    if not ticker:
        return {"error": "ticker is required"}
    if quantity is None:
        return {"error": "quantity is required"}

    price = quote_data.get("price_usd")
    if price is None:
        return {"error": "quote_data.price_usd is required"}

    return {
        "ticker": str(ticker).upper(),
        "quantity": float(quantity),
        "price": float(price),
    }
