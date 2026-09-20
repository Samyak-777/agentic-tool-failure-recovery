"""
execute_quote_snapshot_sell_native Tool Plugin

Function: Execute a sell order from a direct-quote native snapshot
Category: Action
Domain: Financial
"""

TOOL_NAME = "execute_quote_snapshot_sell_native"

from tools.plugins import place_sell_order as pso


def execute(arguments, context) -> dict:
    quote_snapshot = arguments.get("quote_snapshot") or {}
    if not isinstance(quote_snapshot, dict):
        return {"error": "quote_snapshot must be an object"}

    quantity = arguments.get("quantity")
    if quantity is None:
        return {"error": "quantity is required"}

    ticker = quote_snapshot.get("symbol") or "AAPL"
    price = quote_snapshot.get("usd_last", 100.0)

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

    return {
        "status": result.get("status", "filled"),
        "strategy": "direct_quote_sell_native",
        "order_id": result.get("order_id"),
        "ticker": result.get("ticker", ticker),
        "quantity": result.get("quantity", quantity),
        "execution_ref": quote_snapshot.get("snapshot_ref") or "quote_snapshot",
    }
