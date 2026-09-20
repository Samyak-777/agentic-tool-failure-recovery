"""
build_converted_sell_request Tool Plugin

Function: Build a normalized sell-order request from a converted equity quote
Category: Processor
Domain: Financial
"""

TOOL_NAME = "build_converted_sell_request"


def execute(arguments, context) -> dict:
    del context

    converted_quote = arguments.get("converted_quote")
    ticker = arguments.get("ticker")
    quantity = arguments.get("quantity")

    if not isinstance(converted_quote, dict):
        return {"error": "converted_quote must be an object"}
    if not ticker:
        return {"error": "ticker is required"}
    if quantity is None:
        return {"error": "quantity is required"}

    price_usd = converted_quote.get("price_usd")
    if price_usd is None:
        return {"error": "converted_quote.price_usd is required"}

    exchange_rate = converted_quote.get("exchange_rate", 1.0)
    target_currency = converted_quote.get("target_currency") or converted_quote.get("currency", "USD")
    converted_price = round(float(price_usd) * float(exchange_rate), 6)

    return {
        "ticker": str(ticker).upper(),
        "quantity": float(quantity),
        "price_usd": float(price_usd),
        "converted_price": converted_price,
        "target_currency": target_currency,
    }
