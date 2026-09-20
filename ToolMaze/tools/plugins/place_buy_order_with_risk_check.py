"""
place_buy_order_with_risk_check Tool Plugin

Function: Assess risk and execute buy order in one step
Category: Action
Domain: Financial
"""

TOOL_NAME = "place_buy_order_with_risk_check"

from tools.plugins import assess_trade_risk as atr
from tools.plugins import place_buy_order as pbo


def execute(arguments, context) -> dict:
    """先风控再执行买单"""
    amount = arguments.get("amount")
    risk_result = atr.execute({"amount": amount}, context)
    if "error" in risk_result:
        return risk_result

    if risk_result.get("decision") != "approved":
        return {
            "error": f"Trade not approved: {risk_result.get('reason', 'unknown reason')}",
            "decision": risk_result.get("decision"),
            "reason": risk_result.get("reason"),
        }

    order_result = pbo.execute({"risk_token": risk_result.get("risk_token"), "price": amount}, context)
    if "error" in order_result:
        return order_result

    order_result["filled_amount"] = order_result.pop("filled_average_price", None)
    order_result["risk_token"] = risk_result.get("risk_token")
    order_result["risk_decision"] = risk_result.get("decision")
    return order_result
