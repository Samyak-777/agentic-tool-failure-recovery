"""
place_buy_order Tool Plugin
Function: Place a buy order
Category: Action
Domain: Financial
"""
TOOL_NAME = "place_buy_order"

CONSTRAINTS = {}

def execute(arguments, context) -> dict:
    import json

    risk_token = arguments.get("risk_token")

    # Handle both raw string and JSON-formatted string
    if risk_token:
        if isinstance(risk_token, str) and risk_token.startswith('"'):
            try:
                risk_token = json.loads(risk_token)
            except:
                pass

    if not risk_token:
        return {
            "error": "Invalid or missing risk_token. Please call assess_trade_risk first."
        }

    filled_price = arguments.get("price")
    if filled_price is None:
        return {"error": "Missing required parameter: 'price'. Please provide the price per unit for the buy order."}
    
    order_id = "ORD-BUY-FAEF1"

    return {
        "order_id": order_id,
        "action": "BUY",
        "status": "filled",
        "filled_average_price": filled_price,
        "message": "Order executed successfully"
    }