"""
query_catalog Tool Plugin
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


TOOL_NAME = "query_catalog"

CONSTRAINTS = {
    "query": ["sony", "apple", "headphones", "airpods", "electronics", "beverage", "cola", "coca"]
}

def execute(arguments, context) -> dict:
    # Get query (optional parameter)
    query = arguments.get("query") or ""

    # Get category (optional parameter with reasonable default)
    category = arguments.get("category") or "all"

    # Get max_results (optional parameter with reasonable default)
    max_results = arguments.get("max_results") or 10

    # 收集用户浏览过的产品（用于排序优化）
    viewed_products = set()
    if hasattr(context, 'history'):
        for record in context.history:
            if record.tool_name in ["query_catalog", "get_stock_level", "get_recommendations"]:
                pid = record.arguments.get("product_id")
                if pid:
                    viewed_products.add(pid)

    def search_products(query):
        query = query.lower()
        results = []
        for pid, data in products.items():
            if query in data["name"].lower() or query in data["category"]:
                item = data.copy()
                item["id"] = pid
                # 添加相关性分数（已浏览的产品分数更高）
                item["relevance"] = 2 if pid in viewed_products else 1
                del item["stock"]
                results.append(item)
        # 按相关性排序
        results.sort(key=lambda x: x["relevance"], reverse=True)
        # 移除相关性字段（不需要返回给用户）
        for item in results:
            del item["relevance"]
        return results

    results = search_products(query)

    return {
        "query": query,
        "count": len(results),
        "results": results,
        "hint": "Use check_inventory to verify availability."
    }