"""
checkout_best_recommendation Tool Plugin

Function: Hold the best recommendation and confirm checkout in one step
Category: Action
Domain: Shopping
"""

TOOL_NAME = "checkout_best_recommendation"

from tools.plugins import build_checkout_from_hold as bcfh
from tools.plugins import confirm_held_recommendation_order as chro
from tools.plugins import hold_best_recommendation as hbr


def execute(arguments, context) -> dict:
    hold_data = hbr.execute(
        {
            "product_id": arguments.get("product_id"),
            "quantity": arguments.get("quantity") or 1,
            "user_id": arguments.get("user_id"),
            "category": arguments.get("category") or "",
        },
        context,
    )
    if "error" in hold_data:
        return hold_data

    checkout_request = bcfh.execute(
        {
            "hold_data": hold_data,
            "quantity": arguments.get("quantity") or 1,
        },
        context,
    )
    if "error" in checkout_request:
        return checkout_request

    result = chro.execute(
        {
            "reservation_id": checkout_request.get("reservation_id"),
            "product_id": checkout_request.get("product_id"),
            "quantity": checkout_request.get("quantity"),
        },
        context,
    )
    if "error" in result:
        return result

    result["original_product_id"] = hold_data.get("original_product_id")
    result["recommended_product_id"] = hold_data.get("recommended_product_id")
    result["workflow"] = "recommended_checkout"
    return result
