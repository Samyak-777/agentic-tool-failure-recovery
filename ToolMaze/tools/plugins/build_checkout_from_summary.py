"""
build_checkout_from_summary Tool Plugin
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "build_checkout_from_summary"


def execute(arguments, context) -> dict:
    cart_summary = arguments.get("cart_summary") or {}
    items = arguments.get("items")
    user_id = arguments.get("user_id")
    payment_method = arguments.get("payment_method")

    if not isinstance(cart_summary, dict):
        return {"error": "cart_summary must be an object"}
    if not isinstance(items, list) or not items:
        return {"error": "items must be a non-empty list"}
    if not user_id or not payment_method:
        return {"error": "user_id and payment_method are required"}
    if "error" in cart_summary:
        return cart_summary

    return {
        "items": items,
        "payment_amount": cart_summary.get("final_total") or cart_summary.get("payment_amount", 0.0),
        "user_id": user_id,
        "payment_method": payment_method,
        "subtotal": cart_summary.get("subtotal", 0.0),
        "discount": cart_summary.get("discount", 0.0),
        "coupon_status": cart_summary.get("coupon_status", ""),
    }
