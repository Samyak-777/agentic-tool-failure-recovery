"""
optimize_discount Tool Plugin
Category: Processor
Domain: Shopping
Function: Analyze cart and available coupons to find the maximum discount.
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
TOOL_NAME = "optimize_discount"

def execute(arguments, context) -> dict:
    user_id = arguments.get("user_id") or "default_uid"
    coupons_list = arguments.get("coupons_list") or []

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
        return {"error": "Cart is empty", "best_coupon": None}

    # 1. Calculate Cart Subtotal (Needed to check thresholds)
    subtotal = 0.0
    for pid, qty in cart_data.items():
        p_data = products[pid]
        if p_data:
            subtotal += p_data["price"] * qty

    # 2. If no list provided, fetch all from DB (Robustness fallback)
    if len(coupons_list) == 0:
        return {"error": "Didn't receive any coupons", "best_coupon": None}
    
    best_coupon = None
    max_savings = 0.0
    evaluated_coupons = []

    for item in coupons_list:
        code = item.get("code") if isinstance(item, dict) else str(item)
        
        rule = coupons[code]
        if not rule:
            continue
            
        savings = 0.0
        min_spend = rule.get("min_spend", 0)
        
        # Check eligibility
        is_applicable = subtotal >= min_spend
        
        if is_applicable:
            if rule["type"] == "fixed":
                savings = rule["amount"]
            elif rule["type"] == "percent":
                savings = subtotal * rule["amount"]
        
        # Track logic
        evaluated_coupons.append({
            "code": code,
            "potential_savings": round(savings, 2),
            "applicable": is_applicable,
            "reason": "Threshold not met" if not is_applicable else "Valid"
        })

        # Update best candidate
        if is_applicable and savings > max_savings:
            max_savings = savings
            best_coupon = code

    return {
        "cart_subtotal": round(subtotal, 2),
        "best_coupon_code": best_coupon,
        "estimated_savings": round(max_savings, 2),
        "final_total": round(subtotal - max_savings, 2)
    }