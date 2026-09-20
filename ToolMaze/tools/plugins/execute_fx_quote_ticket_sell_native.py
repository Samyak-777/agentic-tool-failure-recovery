"""
execute_fx_quote_ticket_sell_native Tool Plugin

Function: Execute a sell order from an FX-quote native ticket
Category: Action
Domain: Financial
"""

TOOL_NAME = "execute_fx_quote_ticket_sell_native"

from tools.plugins import place_sell_order as pso


def execute(arguments, context) -> dict:
    fx_quote_ticket = arguments.get("fx_quote_ticket") or {}
    if not isinstance(fx_quote_ticket, dict):
        return {"error": "fx_quote_ticket must be an object"}

    quantity = arguments.get("quantity")
    if quantity is None:
        return {"error": "quantity is required"}

    ticker = fx_quote_ticket.get("ticker_code") or "AAPL"
    price = fx_quote_ticket.get("usd_reference", 100.0)

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
        "strategy": "fx_quote_sell_native",
        "order_id": result.get("order_id"),
        "ticker": result.get("ticker", ticker),
        "quantity": result.get("quantity", quantity),
        "execution_ref": fx_quote_ticket.get("ticket_ref") or "fx_quote_ticket",
    }
