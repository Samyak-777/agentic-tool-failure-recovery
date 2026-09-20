"""
generate_invoice_from_summary Tool Plugin
Category: Action
Domain: Shopping
"""

TOOL_NAME = "generate_invoice_from_summary"

from tools.plugins import generate_payment_invoice as gpi


def execute(arguments, context) -> dict:
    result = gpi.execute(
        {
            "items": arguments.get("items"),
            "payment_amount": arguments.get("payment_amount"),
            "user_id": arguments.get("user_id"),
            "email": arguments.get("email"),
            "payment_gateway": arguments.get("payment_gateway"),
        },
        context,
    )
    if "error" in result:
        return result

    result["cart_subtotal"] = arguments.get("subtotal", 0.0)
    result["cart_discount"] = arguments.get("discount", 0.0)
    result["coupon_status"] = arguments.get("coupon_status", "")
    return result
