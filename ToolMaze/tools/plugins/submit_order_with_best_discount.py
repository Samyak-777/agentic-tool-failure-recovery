"""
submit_order_with_best_discount Tool Plugin

Function: Automatically apply the best available coupon and submit the order
Category: Action
Domain: Shopping
"""

TOOL_NAME = "submit_order_with_best_discount"

CONSTRAINTS = {
    "payment_method": [
        "credit_card",
        "debit_card",
        "paypal",
        "apple_pay",
        "google_pay",
        "bank_transfer",
    ]
}

from tools.plugins import get_available_coupons as gac
from tools.plugins import optimize_discount as od
from tools.plugins import submit_order as so


def execute(arguments, context) -> dict:
    """自动应用最优优惠券并提交订单"""
    items = arguments.get("items")
    if not isinstance(items, list) or not items:
        return {"error": "items must be a non-empty list"}

    user_id = arguments.get("user_id") or "default_user"
    payment_method = arguments.get("payment_method") or "paypal"

    coupons_result = gac.execute({"user_id": user_id}, context)
    if "error" in coupons_result:
        return coupons_result

    discount_result = od.execute(
        {
            "items": items,
            "coupons_list": coupons_result.get("coupons", []),
            "user_id": user_id,
        },
        context,
    )
    if "error" in discount_result:
        return discount_result

    submit_result = so.execute(
        {
            "items": items,
            "payment_amount": discount_result.get("final_total", 0.0),
            "user_id": user_id,
            "payment_method": payment_method,
        },
        context,
    )
    if "error" in submit_result:
        return submit_result

    submit_result["best_coupon_code"] = discount_result.get("best_coupon_code")
    submit_result["estimated_savings"] = discount_result.get("estimated_savings")
    submit_result["cart_subtotal"] = discount_result.get("cart_subtotal")
    return submit_result
