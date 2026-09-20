"""
get_recommendations Tool Plugin
Category: Source
Domain: Shopping
"""

products = {
    "p_sony_xm5_blk": {
        "name": "Sony WH-1000XM5 Headphones (Black)",
        "price": 399.00,
        "category": "electronics",
        "tags": ["audio", "sony", "headphone"],
        "stock": 10,
    },
    "p_sony_xm5_slv": {
        "name": "Sony WH-1000XM5 Headphones (Silver)",
        "price": 399.00,
        "category": "electronics",
        "tags": ["audio", "sony", "headphone"],
        "stock": 10,
    },
    "p_apple_airpods": {
        "name": "Apple AirPods Pro 2",
        "price": 249.00,
        "category": "electronics",
        "tags": ["audio", "apple", "earbuds"],
        "stock": 50,
    },
    "p_coke_500": {
        "name": "Coca-Cola 500ml",
        "price": 1.50,
        "category": "beverage",
        "tags": ["drink", "cola", "bottle"],
        "stock": 100,
    },
}

TOOL_NAME = "get_recommendations"

ALTERNATIVE_TOOLS = [
    "get_recommendations",
    "get_recommendations_collaborative",
    "get_recommendations_content",
    "get_recommendations_popularity",
    "get_recommendations_trending",
]

CONSTRAINTS = {
    "product_id": ["p_sony_xm5_blk", "p_sony_xm5_slv", "p_apple_airpods", "p_coke_500"]
}



def _collect_user_signals(context):
    viewed_products = set()
    cart_products = set()
    if not hasattr(context, "history"):
        return viewed_products, cart_products

    for record in context.history:
        if record.tool_name in ["query_catalog", "get_stock_level"]:
            product_id = record.arguments.get("product_id")
            if product_id:
                viewed_products.add(product_id)
        elif record.tool_name == "add_to_cart":
            product_id = record.arguments.get("product_id")
            if product_id:
                cart_products.add(product_id)

    return viewed_products, cart_products



def _build_recommendations_result(product_id, category, user_id, context):
    del user_id

    if not product_id:
        similar_items = []
        for candidate_id, data in products.items():
            if category != "all" and data.get("category") != category:
                continue
            if data.get("stock", 0) <= 0:
                continue

            item = dict(data)
            item["id"] = candidate_id
            item["relevance_score"] = 1
            similar_items.append(item)

        similar_items.sort(key=lambda item: (item["price"], item["id"]))
        return {
            "original_product_id": None,
            "category": category,
            "count": len(similar_items),
            "similar_products": similar_items,
            "message": f"Found {len(similar_items)} products in category '{category}'.",
        }

    target_product = products.get(product_id)
    if not target_product:
        return {"error": "Target product not found", "results": []}

    viewed_products, cart_products = _collect_user_signals(context)
    target_category = target_product.get("category")
    target_tags = set(target_product.get("tags", []))
    similar_items = []

    for candidate_id, data in products.items():
        if candidate_id == product_id or candidate_id in cart_products:
            continue
        if data.get("category") != target_category:
            continue
        if data.get("stock", 0) <= 0:
            continue

        overlap = len(target_tags.intersection(set(data.get("tags", []))))
        if candidate_id in viewed_products:
            overlap += 1

        item = dict(data)
        item["id"] = candidate_id
        item["relevance_score"] = overlap
        similar_items.append(item)

    similar_items.sort(key=lambda item: (-item["relevance_score"], item["price"], item["id"]))
    return {
        "original_product_id": product_id,
        "count": len(similar_items),
        "similar_products": similar_items,
        "message": "Found alternatives in the same category." if similar_items else "No similar products found.",
    }



def execute(arguments, context) -> dict:
    raw_product_id = arguments.get("product_id")
    raw_category = arguments.get("category")
    raw_user_id = arguments.get("user_id")

    if hasattr(context, "find_alternative_output"):
        args_match = {}
        if raw_product_id is not None:
            args_match["product_id"] = raw_product_id
        if raw_category is not None:
            args_match["category"] = raw_category
        if raw_user_id is not None:
            args_match["user_id"] = raw_user_id
        if args_match:
            existing = context.find_alternative_output(ALTERNATIVE_TOOLS, args_match)
            if existing:
                return existing

    category = raw_category or "all"
    user_id = raw_user_id or "default_user"
    return _build_recommendations_result(raw_product_id, category, user_id, context)
