"""
generate_invoice_with_best_discount Tool Plugin

Function: Automatically apply the best coupon and generate an invoice
Category: Action
Domain: Shopping
"""

TOOL_NAME = "generate_invoice_with_best_discount"

CONSTRAINTS = {
    "payment_gateway": ["stripe", "paypal", "square", "alipay", "wechat_pay"],
}

from tools.plugins import get_available_coupons as gac
from tools.plugins import optimize_discount as od
from tools.plugins import generate_payment_invoice as gpi


def execute(arguments, context) -> dict:
    """Apply the best coupon and generate an invoice."""
    items = arguments.get("items")
    if not isinstance(items, list) or not items:
        return {"error": "items must be a non-empty list"}

    user_id = arguments.get("user_id") or "default_user"
    email = arguments.get("email") or "alice@company.com"
    payment_gateway = arguments.get("payment_gateway") or "paypal"

    coupon_result = gac.execute({"user_id": user_id}, context)
    if "error" in coupon_result:
        return coupon_result

    discount_result = od.execute(
        {
            "items": items,
            "user_id": user_id,
            "coupons_list": coupon_result.get("coupons", []),
        },
        context,
    )
    if "error" in discount_result:
        return discount_result

    invoice_result = gpi.execute(
        {
            "items": items,
            "payment_amount": discount_result.get("final_total", 0.0),
            "user_id": user_id,
            "email": email,
            "payment_gateway": payment_gateway,
        },
        context,
    )
    if "error" in invoice_result:
        return invoice_result

    invoice_result["best_coupon_code"] = discount_result.get("best_coupon_code")
    invoice_result["estimated_savings"] = discount_result.get("estimated_savings")
    invoice_result["cart_subtotal"] = discount_result.get("cart_subtotal")
    return invoice_result
