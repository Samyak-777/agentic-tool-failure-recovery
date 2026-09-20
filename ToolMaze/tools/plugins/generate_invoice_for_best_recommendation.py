"""
generate_invoice_for_best_recommendation Tool Plugin

Function: Hold the best recommendation and generate an invoice in one step
Category: Action
Domain: Shopping
"""

TOOL_NAME = "generate_invoice_for_best_recommendation"

from tools.plugins import build_invoice_from_hold as bifh
from tools.plugins import generate_invoice_from_hold as gifh
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

    invoice_request = bifh.execute(
        {
            "hold_data": hold_data,
            "quantity": arguments.get("quantity") or 1,
            "user_id": arguments.get("user_id"),
            "email": arguments.get("email"),
            "payment_gateway": arguments.get("payment_gateway"),
        },
        context,
    )
    if "error" in invoice_request:
        return invoice_request

    result = gifh.execute(
        {
            "items": invoice_request.get("items"),
            "payment_amount": invoice_request.get("payment_amount"),
            "user_id": invoice_request.get("user_id"),
            "email": invoice_request.get("email"),
            "payment_gateway": invoice_request.get("payment_gateway"),
            "reservation_id": invoice_request.get("reservation_id"),
        },
        context,
    )
    if "error" in result:
        return result

    result["original_product_id"] = hold_data.get("original_product_id")
    result["recommended_product_id"] = hold_data.get("recommended_product_id")
    result["workflow"] = "recommended_invoice"
    return result
