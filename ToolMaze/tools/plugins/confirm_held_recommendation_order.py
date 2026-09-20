"""
confirm_held_recommendation_order Tool Plugin
Category: Action
Domain: Shopping
"""

TOOL_NAME = "confirm_held_recommendation_order"

from tools.plugins import confirm_order as co


def execute(arguments, context) -> dict:
    result = co.execute(
        {
            "reservation_id": arguments.get("reservation_id"),
            "product_id": arguments.get("product_id"),
            "quantity": arguments.get("quantity") or 1,
        },
        context,
    )
    if "error" in result:
        return result

    result["confirmation_strategy"] = "held_recommendation"
    return result
