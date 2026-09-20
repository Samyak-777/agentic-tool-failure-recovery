"""
resolve_converted_quote_profile Tool Plugin

Function: Resolve a normalized quote profile from a converted equity quote
Category: Processor
Domain: Financial
"""

TOOL_NAME = "resolve_converted_quote_profile"


def execute(arguments, context) -> dict:
    del context

    converted_quote = arguments.get("converted_quote")
    if not isinstance(converted_quote, dict):
        return {"error": "converted_quote must be an object"}

    display_price = converted_quote.get("price")
    display_currency = converted_quote.get("currency")
    if display_price is None or not display_currency:
        return {"error": "converted_quote.price and converted_quote.currency are required"}

    ticker = (arguments.get("ticker") or "").upper()
    if not ticker:
        return {"error": "ticker is required"}

    reference_price_usd = converted_quote.get("price_usd", display_price if display_currency == "USD" else None)
    if reference_price_usd is None:
        return {"error": "converted_quote.price_usd is required for non-USD conversions"}

    return {
        "pricing_mode": "converted_quote",
        "ticker": ticker,
        "reference_price_usd": reference_price_usd,
        "display_price": display_price,
        "display_currency": display_currency,
    }
