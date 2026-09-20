"""
build_invoice_from_summary Tool Plugin
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "build_invoice_from_summary"


def execute(arguments, context) -> dict:
    cart_summary = arguments.get("cart_summary") or {}
    items = arguments.get("items")
    user_id = arguments.get("user_id")
    email = arguments.get("email")
    payment_gateway = arguments.get("payment_gateway")

    if not isinstance(cart_summary, dict):
        return {"error": "cart_summary must be an object"}
    if not isinstance(items, list) or not items:
        return {"error": "items must be a non-empty list"}
    if not user_id or not email or not payment_gateway:
        return {"error": "user_id, email, and payment_gateway are required"}
    if "error" in cart_summary:
        return cart_summary

    return {
        "items": items,
        "payment_amount": cart_summary.get("final_total", 0.0),
        "user_id": user_id,
        "email": email,
        "payment_gateway": payment_gateway,
        "subtotal": cart_summary.get("subtotal", 0.0),
        "discount": cart_summary.get("discount", 0.0),
        "coupon_status": cart_summary.get("coupon_status", ""),
    }
