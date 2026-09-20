"""
generate_invoice_from_hold Tool Plugin
Category: Action
Domain: Shopping
"""

TOOL_NAME = "generate_invoice_from_hold"

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

    result["reservation_id"] = arguments.get("reservation_id") or ""
    result["invoice_strategy"] = "held_recommendation"
    return result
