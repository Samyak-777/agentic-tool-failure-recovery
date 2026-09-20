"""
place_sell_order Tool Plugin
Function: Place a sell order
Category: Action
Domain: Financial
"""
CASES = {
    "AAPL": {"price_usd": 170.25, "currency": "USD"},
    "GOOGL": {"price_usd": 138.40, "currency": "USD"},
    "TSLA": {"price_usd": 245.10, "currency": "USD"},
    "MSFT": {"price_usd": 330.75, "currency": "USD"},
    "AMZN": {"price_usd": 140.60, "currency": "USD"},
}

TOOL_NAME = "place_sell_order"

CONSTRAINTS = {
    "ticker": list(CASES.keys())
}

def execute(arguments, context) -> dict:
    # Get ticker (required parameter)
    ticker = arguments.get("ticker")
    if not ticker:
        return {"error": "ticker is required"}

    ticker = ticker.upper()

    if ticker not in CASES:
        return {"error": f"Invalid ticker '{ticker}'"}

    # Get quantity (optional parameter with reasonable default)
    quantity = arguments.get("quantity") or 1.0

    # Get stock price from arguments, fallback to hardcoded default
    stock_price = arguments.get("price") or CASES[ticker]["price_usd"]

    order_id = "ORD-SELL-FAEF1"

    # Mock PnL calculation - 使用从 context 获取的价格
    realized_pnl = float(quantity) * float(stock_price)

    return {
        "order_id": order_id,
        "ticker": ticker,
        "action": "SELL",
        "quantity": quantity,
        "status": "filled",
        "realized_pnl": realized_pnl,
        "message": "Order executed successfully"
    }