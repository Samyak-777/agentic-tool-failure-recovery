"""
resolve_direct_quote_profile Tool Plugin

Function: Resolve a normalized quote profile from a direct equity quote
Category: Processor
Domain: Financial
"""

TOOL_NAME = "resolve_direct_quote_profile"


def execute(arguments, context) -> dict:
    del context

    quote_data = arguments.get("quote_data")
    if not isinstance(quote_data, dict):
        return {"error": "quote_data must be an object"}

    price_usd = quote_data.get("price_usd")
    if price_usd is None:
        return {"error": "quote_data.price_usd is required"}

    ticker = (arguments.get("ticker") or "").upper()
    if not ticker:
        return {"error": "ticker is required"}

    return {
        "pricing_mode": "direct_quote",
        "ticker": ticker,
        "reference_price_usd": price_usd,
        "display_price": price_usd,
        "display_currency": quote_data.get("currency") or "USD",
    }
