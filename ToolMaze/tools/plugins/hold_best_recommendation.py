"""
hold_best_recommendation Tool Plugin

Function: Select the best recommendation and reserve it
Category: Source
Domain: Shopping
"""

TOOL_NAME = "hold_best_recommendation"

from tools.plugins import get_recommendations as gr
from tools.plugins import select_recommendation as sr
from tools.plugins import hold_inventory as hi

CONSTRAINTS = gr.CONSTRAINTS


def execute(arguments, context) -> dict:
    """Choose the best recommendation and reserve it."""
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

    recommendation_result = gr.execute(
        {
            "product_id": product_id,
            "category": category,
            "user_id": user_id,
        },
        context,
    )
    if "error" in recommendation_result:
        return recommendation_result

    selection_result = sr.execute(
        {
            "similar_products": recommendation_result.get("similar_products", []),
            "quantity": quantity,
        },
        context,
    )
    if "error" in selection_result:
        return selection_result

    hold_result = hi.execute(
        {
            "product_id": selection_result.get("product_id"),
            "quantity": quantity,
            "user_id": user_id,
        },
        context,
    )
    if "error" in hold_result:
        return hold_result

    hold_result["original_product_id"] = product_id
    hold_result["recommended_product_id"] = selection_result.get("product_id")
    hold_result["recommended_product_name"] = selection_result.get("name")
    hold_result["selection_reason"] = selection_result.get("selection_reason")
    hold_result["selected_relevance_score"] = selection_result.get("relevance_score")
    return hold_result
