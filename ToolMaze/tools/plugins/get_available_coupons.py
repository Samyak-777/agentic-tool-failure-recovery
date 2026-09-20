"""
get_available_coupons Tool Plugin
Category: Source
Domain: Shopping
Function: List all active coupons for the user to select.
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
TOOL_NAME = "get_available_coupons"

def execute(arguments, context) -> dict:
    """
    Retrieve available coupons.
    """
    user_id = arguments.get("user_id")
    if not user_id and hasattr(context, 'history'):
        for record in context.history:
            if record.tool_name == "get_contact_info" and record.output.get("user_id"):
                user_id = record.output["user_id"]
                break
    user_id = user_id or "default_user"

    # 获取已使用的优惠券（从 context.history 中查找）
    used_coupons = set()
    if hasattr(context, 'history'):
        for record in context.history:
            # 检查 get_cart_summary 或 optimize_discount 中使用的优惠券
            if record.tool_name in ["get_cart_summary", "optimize_discount"]:
                coupon_code = record.arguments.get("coupon_code")
                if coupon_code:
                    used_coupons.add(coupon_code)

    raw_coupons = coupons
    
    available_list = []

    for code, rule in raw_coupons.items():
        # 跳过已使用的优惠券
        if code in used_coupons:
            continue

        # Generate a model-friendly description
        desc = ""
        if rule.get("type") == "fixed":
            desc = f"Save ${rule.get('amount', 0):.2f}"
        elif rule.get("type") == "percent":
            desc = f"Save {int(rule.get('amount', 0) * 100)}%"

        min_spend = rule.get("min_spend", 0)
        if min_spend > 0:
            desc += f" on orders over ${min_spend:.2f}"
        else:
            desc += " on any order"

        available_list.append({
            "code": code,
            "description": desc,
            "condition": {
                "min_spend": min_spend,
                "type": rule.get("type")
            }
        })

    return {
        "count": len(available_list),
        "coupons": available_list,
        "user_id": user_id
    }