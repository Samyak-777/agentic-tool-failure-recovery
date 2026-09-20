"""
build_recommended_invoice_request Tool Plugin

Function: Hold the best recommendation and build an invoice request
Category: Processor
Domain: Shopping
"""

TOOL_NAME = "build_recommended_invoice_request"

from tools.plugins import build_invoice_from_hold as bifh
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

    request = bifh.execute(
        {
            "hold_data": hold_data,
            "quantity": arguments.get("quantity") or 1,
            "user_id": arguments.get("user_id"),
            "email": arguments.get("email"),
            "payment_gateway": arguments.get("payment_gateway"),
        },
        context,
    )
    if "error" in request:
        return request

    request["original_product_id"] = hold_data.get("original_product_id")
    request["recommended_product_id"] = hold_data.get("recommended_product_id")
    return request
