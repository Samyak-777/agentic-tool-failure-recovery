"""
hold_inventory Tool Plugin

Function: Reserve inventory for a product without payment
Category: Source
Domain: Shopping
"""

# Hard-coded product data (matches example structure)
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

# Reservation storage (in-memory state)
RESERVATIONS = {}  # reservation_id -> {user_id, product_id, quantity, expiry, total_price}
CONSTRAINTS = {
    "product_id": list(PRODUCTS.keys())
}

TOOL_NAME = "hold_inventory"


def execute(arguments, context) -> dict:
    # Get user_id (optional parameter)
    user_id = arguments.get("user_id")

    # Get product_id (required parameter)
    product_id = arguments.get("product_id")

    if not product_id:
        return {"error": "product_id is required"}

    # Get quantity (optional parameter with reasonable default)
    quantity = arguments.get("quantity") or 1

    # 1. Input validation
    
    try:
        quantity = int(quantity)
        if quantity < 1:
            return {"error": "Quantity must be at least 1"}
    except (TypeError, ValueError):
        return {"error": "Invalid quantity value"}
    
    # 2. Get current timestamp (simulate time)
    current_time = 1710000000
    
    # 4. Validate product and inventory
    product = PRODUCTS.get(product_id)
    if not product:
        return {"error": f"Product ID '{product_id}' not found"}
    
    if product["stock"] < quantity:
        # Find similar products as fallback suggestions
        similar_products = []
        target_category = product["category"]
        for pid, pdata in PRODUCTS.items():
            if pid != product_id and pdata["category"] == target_category and pdata["stock"] > 0:
                similar_products.append({
                    "id": pid,
                    "name": pdata["name"],
                    "price": pdata["price"],
                    "stock": pdata["stock"]
                })
                if len(similar_products) >= 3:  # Limit to 3 suggestions
                    break
        
        return {
            "error": f"Insufficient stock for '{product_id}'. Available: {product['stock']}",
            "suggestions": similar_products
        }
    
    reservation_id = "RESV-14729548"
    expiry = current_time + 300  # 5 minutes expiry

    # Calculate total price
    total_price = product["price"] * quantity
    
    # Update inventory and store reservation
    # product["stock"] -= quantity
    # RESERVATIONS[reservation_id] = {
    #     "user_id": user_id,
    #     "product_id": product_id,
    #     "quantity": quantity,
    #     "expiry": expiry,
    #     "total_price": total_price,
    #     "created_at": current_time
    # }
    
    return {
        "reservation_id": reservation_id,
        "expires_in": 300,
        "product_id": product_id,
        "quantity": quantity,
        "total_price": total_price,
        "expiry_time": expiry,
        "reservation_details": {
            "product_id": product_id,
            "quantity": quantity,
            "total_price": total_price
        }
    }