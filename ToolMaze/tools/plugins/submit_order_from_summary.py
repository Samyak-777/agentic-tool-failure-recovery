"""
submit_order_from_summary Tool Plugin
Category: Action
Domain: Shopping
"""

TOOL_NAME = "submit_order_from_summary"

from tools.plugins import submit_order as so


def execute(arguments, context) -> dict:
    result = so.execute(
        {
            "items": arguments.get("items"),
            "payment_amount": arguments.get("payment_amount"),
            "user_id": arguments.get("user_id"),
            "payment_method": arguments.get("payment_method"),
        },
        context,
    )
    if "error" in result:
        return result

    result["cart_subtotal"] = arguments.get("subtotal", 0.0)
    result["cart_discount"] = arguments.get("discount", 0.0)
    result["coupon_status"] = arguments.get("coupon_status", "")
    return result
