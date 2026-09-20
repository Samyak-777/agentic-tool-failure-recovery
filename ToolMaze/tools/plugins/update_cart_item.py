"""
update_cart_item Tool Plugin
Category: Action
Domain: Shopping
"""
products = {
            "p_sony_xm5_blk": {
                "name": "Sony WH-1000XM5 Headphones (Black)",
                "price": 399.00,
                "category": "electronics",
                "tags": ["audio", "sony", "headphone"],
                "stock": 10
            },
            "p_sony_xm5_slv": {
                "name": "Sony WH-1000XM5 Headphones (Silver)",
                "price": 399.00,
                "category": "electronics",
                "tags": ["audio", "sony", "headphone"],
                "stock": 10
            },
            "p_apple_airpods": {
                "name": "Apple AirPods Pro 2",
                "price": 249.00,
                "category": "electronics",
                "tags": ["audio", "apple", "earbuds"],
                "stock": 50
            },
            "p_coke_500": {
                "name": "Coca-Cola 500ml",
                "price": 1.50,
                "category": "beverage",
                "tags": ["drink", "cola", "bottle"],
                "stock": 100
            }
}
coupons = {
            "SAVE15": {"type": "fixed", "amount": 15.0, "min_spend": 100.0},
            "WELCOME10": {"type": "percent", "amount": 0.1, "min_spend": 0.0}
        }
cart = {}

TOOL_NAME = "update_cart_item"

CONSTRAINTS = {
    "product_id": ["p_sony_xm5_blk", "p_sony_xm5_slv", "p_apple_airpods", "p_coke_500"]
}

def execute(arguments, context) -> dict:
    # Get product_id (required parameter)
    product_id = arguments.get("product_id")

    if not product_id:
        return {"error": "product_id is required"}

    # Get user_id (optional parameter)
    user_id = arguments.get("user_id")

    new_quantity = arguments.get("new_quantity")
    if new_quantity is None:
        new_quantity = 1

    try:
        qty = int(new_quantity)
        if qty < 0:
             return {"error": "Quantity cannot be negative"}
    except ValueError:
        return {"error": "new_quantity must be an integer"}

    cart_data = cart.copy()

    action = "update"
    if product_id not in cart_data and qty > 0:
        cart_data[product_id] = qty
        action = "add"
        message = "Item added to cart"
    elif qty == 0:
        if product_id in cart_data:
            del cart_data[product_id]
        action = "remove"
        message = "Item removed from cart"
    else:
        cart_data[product_id] = qty
        message = "Cart item updated"

    return {
        "message": message,
        "product_id": product_id,
        "new_quantity": qty,
        "action": action,
        "cart": cart_data,
        "cart_items": cart_data,
        "cart_summary": {"total_items": sum(cart_data.values())}
    }