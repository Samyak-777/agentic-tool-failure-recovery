"""
submit_order Tool Plugin
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

TOOL_NAME = "submit_order"

CONSTRAINTS = {
    "payment_method": ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay", "bank_transfer"]
}

def execute(arguments, context) -> dict:
    user_id = arguments.get("user_id")
    payment_amount = arguments.get("payment_amount")
    if payment_amount is None:
        payment_amount = 0.0
    payment_method = arguments.get("payment_method") or "paypal"

    # Priority 1: explicit items parameter from caller
    items_arg = arguments.get("items")
    cart_data = None
    if items_arg and isinstance(items_arg, list):
        cart_data = {}
        for item in items_arg:
            pid = item.get("product_id")
            qty = item.get("quantity", 1)
            if pid:
                cart_data[pid] = qty

    # Priority 2: reservation from hold_inventory context
    if not cart_data:
        reservation_id = arguments.get("reservation_id")
        if reservation_id and hasattr(context, 'history'):
            for record in context.history:
                if record.tool_name == "hold_inventory" and record.output.get("reservation_id") == reservation_id:
                    pid = record.output.get("product_id") or record.arguments.get("product_id")
                    qty = record.arguments.get("quantity", 1)
                    if pid:
                        cart_data = {pid: qty}
                    break

    if not cart_data:
        return {"error": "Cannot submit order: no items specified"}

    # Calculate final details
    order_items = []
    total_price_ = 0.0

    for pid, qty in cart_data.items():
        p_data = products.get(pid)
        if p_data:
            cost = p_data["price"] * qty
            total_price_ += cost
            order_items.append({
                "product_id": pid,
                "name": p_data["name"],
                "quantity": qty,
                "subtotal": cost
            })

    if payment_amount and payment_amount != 0.0:
        total_price_ = payment_amount

    order_id = "ORD-8B2C1D3E"

    return {
        "order_id": order_id,
        "status": "confirmed",
        "total_amount": total_price_,
        "items": order_items,
    }
