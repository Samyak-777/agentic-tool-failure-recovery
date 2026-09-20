"""
get_quote_snapshot_native Tool Plugin

Function: Retrieve a direct-quote snapshot using a quote-board native source
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_quote_snapshot_native"

from tools.plugins import get_stock_yahoo_finance as gsyf

CONSTRAINTS = gsyf.CONSTRAINTS


def execute(arguments, context) -> dict:
    ticker = (arguments.get("ticker") or "").upper()
    if not ticker:
        return {"error": "ticker is required"}

    quote = gsyf.execute({"ticker": ticker}, context)
    if "error" in quote:
        return quote

    return {
        "snapshot_ref": f"qs_{ticker.lower()}",
        "symbol": ticker,
        "usd_last": quote.get("price_usd", 0.0),
        "venue": "yahoo_native",
        "quoted_at": "2026-02-22T15:04:54Z",
    }
