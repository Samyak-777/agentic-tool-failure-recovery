"""
get_cart_summary Tool Plugin
Category: Processor
Domain: Shopping
"""
TOOL_NAME = "get_cart_summary"

CONSTRAINTS = {
    "coupon_code": ["SAVE15", "WELCOME10"]
}

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
def execute(arguments, context) -> dict:
    user_id = arguments.get("user_id")
    coupon_code = arguments.get("coupon_code")

    # Build cart from explicit items parameter
    items_arg = arguments.get("items")
    cart_data = {}
    if items_arg and isinstance(items_arg, list):
        for item in items_arg:
            pid = item.get("product_id")
            qty = item.get("quantity", 1)
            if pid:
                cart_data[pid] = qty

    if not cart_data:
        return {"total": 0.0, "items": [], "error": "No items specified"}

    # Calculate Subtotal
    subtotal = 0.0
    details = []

    for pid, qty in cart_data.items():
        p_data = products.get(pid)
        cost = p_data["price"] * qty
        subtotal += cost
        details.append({"product": p_data["name"], "qty": qty, "cost": cost})

    # Apply Coupon
    discount = 0.0
    message = "No coupon applied"
    
    if coupon_code:
        rule = coupons.get(coupon_code)
        if not rule:
            message = f"Coupon '{coupon_code}' is invalid"
        elif subtotal < rule["min_spend"]:
            message = f"Coupon requirement not met: Min spend {rule['min_spend']}"
        else:
            if rule["type"] == "fixed":
                discount = rule["amount"]
            elif rule["type"] == "percent":
                discount = subtotal * rule["amount"]
            message = "Coupon applied successfully"

    final_total = max(0, subtotal - discount)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "final_total": final_total,
        "coupon_status": message,
        "item_count": len(details)
    }