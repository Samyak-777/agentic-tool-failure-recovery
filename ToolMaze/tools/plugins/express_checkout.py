"""
express_checkout Tool Plugin (Variant)
Function: Shortcut for adding to cart and submitting order immediately for a single item.
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

TOOL_NAME = "express_checkout"

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

    # Get quantity (optional parameter with reasonable default)
    quantity = arguments.get("quantity") or 1

    # Get payment_method (optional parameter with reasonable default)
    payment_method = arguments.get("payment_method") or "credit_card"

    product = products.get(product_id)

    if not product:
        return {"error": f"Product with id '{product_id}' does not exist."}

    price = product.get("price", 0.0)
    total_price = price * quantity

    order_id = "QB-7E3A1B2C"

    return {
        "type": "quick_buy_order",
        "order_id": order_id,
        "product_id": product_id,
        "item": product.get("name", "Unknown Product"),
        "quantity": quantity,
        "total_paid": total_price,
        "status": "completed"
    }