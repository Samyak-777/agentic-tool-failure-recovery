"""
select_recommendation Tool Plugin

Function: Choose the best recommendation from a candidate list
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "select_recommendation"



def execute(arguments, context) -> dict:
    """Select the highest-quality recommendation with sufficient stock."""
    del context

    similar_products = arguments.get("similar_products") or []
    quantity = arguments.get("quantity") or 1

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"error": "quantity must be an integer"}

    if quantity <= 0:
        return {"error": "quantity must be positive"}
    if not isinstance(similar_products, list) or not similar_products:
        return {"error": "similar_products must be a non-empty list"}

    candidates = []
    for product in similar_products:
        if not isinstance(product, dict):
            continue

        product_id = product.get("id")
        if not product_id:
            continue

        try:
            stock = int(product.get("stock", 0))
            price = float(product.get("price", 0.0))
            relevance_score = int(product.get("relevance_score", 0))
        except (TypeError, ValueError):
            continue

        if stock < quantity:
            continue

        candidates.append(
            {
                "product_id": product_id,
                "name": product.get("name", product_id),
                "price": price,
                "relevance_score": relevance_score,
                "available_stock": stock,
            }
        )

    if not candidates:
        return {"error": f"No recommended product has enough stock for quantity {quantity}"}

    candidates.sort(
        key=lambda item: (
            -item["relevance_score"],
            item["price"],
            -item["available_stock"],
            item["product_id"],
        )
    )
    selected = candidates[0]
    selected["selection_reason"] = (
        f"Highest relevance recommendation with enough stock for quantity {quantity}"
    )
    return selected
