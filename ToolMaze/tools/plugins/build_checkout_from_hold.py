"""
build_checkout_from_hold Tool Plugin
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "build_checkout_from_hold"


def execute(arguments, context) -> dict:
    hold_data = arguments.get("hold_data") or {}
    quantity = arguments.get("quantity") or 1

    if not isinstance(hold_data, dict):
        return {"error": "hold_data must be an object"}

    reservation_id = hold_data.get("reservation_id")
    product_id = hold_data.get("recommended_product_id") or hold_data.get("product_id")
    if not reservation_id or not product_id:
        return {"error": "hold_data must contain reservation_id and recommended_product_id/product_id"}

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"error": "quantity must be an integer"}

    return {
        "reservation_id": reservation_id,
        "product_id": product_id,
        "quantity": quantity,
    }
