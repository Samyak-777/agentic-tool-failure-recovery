"""
add_best_recommendation_to_cart Tool Plugin

Function: Select the best recommendation and add it to cart
Category: Action
Domain: Shopping
"""

TOOL_NAME = "add_best_recommendation_to_cart"

from tools.plugins import add_to_cart as atc
from tools.plugins import get_recommendations as gr
from tools.plugins import select_recommendation as sr

CONSTRAINTS = gr.CONSTRAINTS



def execute(arguments, context) -> dict:
    """Choose the best recommendation and add it to the user's cart."""
    product_id = arguments.get("product_id")
    if not product_id:
        return {"error": "product_id is required"}

    quantity = arguments.get("quantity") or 1
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return {"error": "quantity must be an integer"}
    if quantity <= 0:
        return {"error": "quantity must be positive"}

    user_id = arguments.get("user_id") or "default_user"
    category = arguments.get("category") or ""

    recommendations_result = gr.execute(
        {
            "product_id": product_id,
            "category": category,
            "user_id": user_id,
        },
        context,
    )
    if "error" in recommendations_result:
        return recommendations_result

    selection_result = sr.execute(
        {
            "similar_products": recommendations_result.get("similar_products", []),
            "quantity": quantity,
        },
        context,
    )
    if "error" in selection_result:
        return selection_result

    cart_result = atc.execute(
        {
            "product_id": selection_result.get("product_id"),
            "quantity": quantity,
            "user_id": user_id,
        },
        context,
    )
    if "error" in cart_result:
        return cart_result

    cart_result["original_product_id"] = product_id
    cart_result["recommended_product_id"] = selection_result.get("product_id")
    cart_result["recommended_product_name"] = selection_result.get("name")
    cart_result["selection_reason"] = selection_result.get("selection_reason")
    cart_result["selected_relevance_score"] = selection_result.get("relevance_score")
    return cart_result
