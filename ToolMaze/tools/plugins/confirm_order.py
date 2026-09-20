"""
confirm_order Tool Plugin

Function: Complete payment for a reserved item
Category: Action
Domain: Shopping
"""

# Hard-coded product data (same as reserve_stock to maintain state)
PRODUCTS = {
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
CONSTRAINTS = {}

# Reservation storage (in-memory state)
RESERVATIONS = {}

TOOL_NAME = "confirm_order"


def execute(arguments, context) -> dict:
    # 优先从 context 获取 reservation_id（可能来自前序的 hold_inventory 等操作）
    reservation_id = arguments.get("reservation_id")

    # 只验证真正必填的参数（required: ["reservation_id"]）
    if not reservation_id:
        return {
            "error": "reservation_id is required"
        }

    product_id = arguments.get("product_id")
    quantity = arguments.get("quantity", 1)

    order_id = "ORD-5C8E2A1B"

    return {
        "order_id": order_id,
        "reservation_id": reservation_id,
        "product_id": product_id,
        "quantity": quantity,
        "status": "confirmed",
        "estimated_delivery": "3-5 business days"
    }