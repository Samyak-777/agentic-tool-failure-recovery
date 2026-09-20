"""
build_cart_items_from_selection Tool Plugin
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "build_cart_items_from_selection"


def execute(arguments, context) -> dict:
    selected_product = arguments.get("selected_product") or {}
    quantity = arguments.get("quantity") or 1

    if not isinstance(selected_product, dict):
        return {"error": "selected_product must be an object"}

    product_id = selected_product.get("product_id") or selected_product.get("id")
    if not product_id:
        return {"error": "selected_product must contain product_id"}

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"error": "quantity must be an integer"}

    if quantity <= 0:
        return {"error": "quantity must be positive"}

    items = [{"product_id": product_id, "quantity": quantity}]
    return {
        "items": items,
        "product_id": product_id,
        "quantity": quantity,
    }
