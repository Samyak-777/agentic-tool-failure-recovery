"""
generate_payment_invoice Tool Plugin (Substitute for submit_order)
Function: Generates an online payment link/invoice for the current cart.
Category: Action
Domain: Shopping
"""
products = {
            "p_sony_xm5_blk": {
                "name": "Sony WH-1000XM5 Headphones (Black)",
                "price": 399.00,
                "category": "electronics",
                "tags": ["audio", "sony", "headphone"],
                "stock": 10
            },
            "p_sony_xm5_slv": {
                "name": "Sony WH-1000XM5 Headphones (Silver)",
                "price": 399.00,
                "category": "electronics",
                "tags": ["audio", "sony", "headphone"],
                "stock": 10
            },
            "p_apple_airpods": {
                "name": "Apple AirPods Pro 2",
                "price": 249.00,
                "category": "electronics",
                "tags": ["audio", "apple", "earbuds"],
                "stock": 50
            },
            "p_coke_500": {
                "name": "Coca-Cola 500ml",
                "price": 1.50,
                "category": "beverage",
                "tags": ["drink", "cola", "bottle"],
                "stock": 100
            }
}
coupons = {
            "SAVE15": {"type": "fixed", "amount": 15.0, "min_spend": 100.0},
            "WELCOME10": {"type": "percent", "amount": 0.1, "min_spend": 0.0}
        }
cart = {}

TOOL_NAME = "generate_payment_invoice"

CONSTRAINTS = {
    "payment_gateway": ["stripe", "paypal", "square", "alipay", "wechat_pay"]
}

def execute(arguments, context) -> dict:
    user_id = arguments.get("user_id")
    email = arguments.get("email")
    payment_gateway = arguments.get("payment_gateway") or "paypal"
    payment_amount = arguments.get("payment_amount")
    if payment_amount is None:
        payment_amount = 0.0

    # Build cart from explicit items parameter
    items_arg = arguments.get("items")
    cart_data = {}
    if items_arg and isinstance(items_arg, list):
        for item in items_arg:
            pid = item.get("product_id")
            qty = item.get("quantity", 1)
            if pid:
                cart_data[pid] = qty

    if not cart_data:
        return {"error": "Cannot generate invoice: no items specified"}

    invoice_id = "INV-F685ABC9"
    payment_link = f"https://pay.example.com/{payment_gateway}/{invoice_id}"

    return {
        "invoice_id": invoice_id,
        "status": "generated",
        "total_due": round(payment_amount, 2),
        "currency": "USD",
        "billing_email": email,
        "payment_link": payment_link,
        "message": "Invoice generated. Please complete payment via the link."
    }