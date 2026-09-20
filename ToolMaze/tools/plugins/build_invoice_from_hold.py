"""
build_invoice_from_hold Tool Plugin
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "build_invoice_from_hold"

PRODUCTS = {
    "p_sony_xm5_blk": 399.00,
    "p_sony_xm5_slv": 399.00,
    "p_apple_airpods": 249.00,
    "p_coke_500": 1.50,
}


def execute(arguments, context) -> dict:
    hold_data = arguments.get("hold_data") or {}
    quantity = arguments.get("quantity") or 1

    if not isinstance(hold_data, dict):
        return {"error": "hold_data must be an object"}

    product_id = hold_data.get("recommended_product_id") or hold_data.get("product_id")
    reservation_id = hold_data.get("reservation_id")
    if not product_id or not reservation_id:
        return {"error": "hold_data must contain recommended_product_id/product_id and reservation_id"}

    user_id = arguments.get("user_id")
    email = arguments.get("email")
    payment_gateway = arguments.get("payment_gateway")
    if not user_id or not email or not payment_gateway:
        return {"error": "user_id, email, and payment_gateway are required"}

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"error": "quantity must be an integer"}

    unit_price = PRODUCTS.get(product_id, 0.0)
    payment_amount = round(unit_price * quantity, 2)
    items = [{"product_id": product_id, "quantity": quantity}]

    return {
        "items": items,
        "payment_amount": payment_amount,
        "reservation_id": reservation_id,
        "user_id": user_id,
        "email": email,
        "payment_gateway": payment_gateway,
    }
