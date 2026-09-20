"""
generate_invoice_from_cart Tool Plugin

Function: Calculate cart total and generate invoice
Category: Action
Domain: Shopping
"""

TOOL_NAME = "generate_invoice_from_cart"

CONSTRAINTS = {
    "payment_gateway": ["stripe", "paypal", "square", "alipay", "wechat_pay"],
    "coupon_code": ["SAVE15", "WELCOME10"],
}

from tools.plugins import get_cart_summary as gcs
from tools.plugins import generate_payment_invoice as gpi


def execute(arguments, context) -> dict:
    """Summarize the cart and generate an invoice."""
    items = arguments.get("items")
    if not isinstance(items, list) or not items:
        return {"error": "items must be a non-empty list"}

    user_id = arguments.get("user_id") or "default_user"
    email = arguments.get("email") or "alice@company.com"
    payment_gateway = arguments.get("payment_gateway") or "paypal"
    coupon_code = arguments.get("coupon_code") or ""

    summary_result = gcs.execute(
        {
            "items": items,
            "user_id": user_id,
            "coupon_code": coupon_code,
        },
        context,
    )
    if "error" in summary_result:
        return summary_result

    invoice_result = gpi.execute(
        {
            "items": items,
            "payment_amount": summary_result.get("final_total", 0.0),
            "user_id": user_id,
            "email": email,
            "payment_gateway": payment_gateway,
        },
        context,
    )
    if "error" in invoice_result:
        return invoice_result

    invoice_result["cart_subtotal"] = summary_result.get("subtotal")
    invoice_result["cart_discount"] = summary_result.get("discount")
    invoice_result["coupon_status"] = summary_result.get("coupon_status")
    invoice_result["item_count"] = summary_result.get("item_count")
    return invoice_result
