"""
get_stock_level Tool Plugin
Category: Source
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

TOOL_NAME = "get_stock_level"

CONSTRAINTS = {
    "product_id": ["p_sony_xm5_blk", "p_sony_xm5_slv", "p_apple_airpods", "p_coke_500"]
}

def execute(arguments, context) -> dict:
    # 只验证真正必填的参数（required: ["product_id"]）
    product_id = arguments.get("product_id")

    if not product_id:
        return {"error": "product_id is required"}

    product = products.get(product_id, None)

    if not product:
        return {"status": "not_found", "stock": 0}

    # 获取初始库存
    stock = product["stock"]

    # 根据 context.history 中的订单记录调整库存
    if hasattr(context, 'history'):
        for record in context.history:
            # 处理提交订单（减少库存）
            if record.tool_name == "submit_order" and "error" not in record.output:
                items = record.output.get("items", [])
                for item in items:
                    if item.get("product_id") == product_id:
                        stock -= item.get("quantity", 0)

            # 处理锁定库存（减少可用库存）
            elif record.tool_name == "hold_inventory" and "error" not in record.output:
                if record.output.get("product_id") == product_id:
                    stock -= record.output.get("quantity", 0)

    # 确保库存不为负数
    stock = max(0, stock)
    status = "in_stock" if stock > 0 else "out_of_stock"

    return {
        "product_id": product_id,
        "name": product["name"],
        "stock": stock,
        "status": status,
        "low_stock_warning": stock < 5 and stock > 0
    }