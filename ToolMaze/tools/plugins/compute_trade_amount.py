"""
compute_trade_amount Tool Plugin
Category: Processor
Domain: Financial
"""

TOOL_NAME = "compute_trade_amount"


def execute(arguments, context) -> dict:
    price_data = arguments.get("price_data") or {}
    quantity = arguments.get("quantity")

    if not isinstance(price_data, dict):
        return {"error": "price_data must be an object"}

    unit_price = price_data.get("price_usd")
    if unit_price is None:
        return {"error": "price_data.price_usd is required"}

    try:
        unit_price = float(unit_price)
        quantity = float(quantity)
    except (TypeError, ValueError):
        return {"error": "unit_price and quantity must be numeric"}

    amount = unit_price * quantity
    return {
        "symbol": price_data.get("symbol", "UNKNOWN"),
        "unit_price": unit_price,
        "quantity": quantity,
        "amount": round(amount, 2),
    }
