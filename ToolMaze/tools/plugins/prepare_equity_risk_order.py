"""
prepare_equity_risk_order Tool Plugin
Category: Processor
Domain: Financial
"""

TOOL_NAME = "prepare_equity_risk_order"


def execute(arguments, context) -> dict:
    market_data = arguments.get("market_data") or {}
    stock_data = arguments.get("stock_data") or {}
    ticker = (arguments.get("ticker") or "").upper()
    quantity = arguments.get("quantity")

    if not isinstance(market_data, dict) or not isinstance(stock_data, dict):
        return {"error": "market_data and stock_data must be objects"}
    if not market_data.get("is_open"):
        return {"error": f"Market for {market_data.get('exchange', ticker)} is closed"}

    try:
        quantity = float(quantity)
        limit_price = float(stock_data.get("price_usd"))
    except (TypeError, ValueError):
        return {"error": "quantity and stock_data.price_usd must be numeric"}

    return {
        "ticker": ticker,
        "quantity": quantity,
        "limit_price": limit_price,
        "amount": round(limit_price * quantity, 2),
        "market_session": market_data.get("session", "unknown"),
    }
