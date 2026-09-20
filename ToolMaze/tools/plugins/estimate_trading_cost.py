"""
estimate_trading_cost Tool Plugin
Function: Calculate trading fees
Category: Processor
Domain: Financial
"""

TOOL_NAME = "estimate_trading_cost"

CONSTRAINTS = {
    "asset_type": ["stock", "crypto", "forex"],
    "user_tier": ["standard", "vip"]
}

def execute(arguments, context) -> dict:
    """计算交易费用"""
    # Get amount (from arguments)
    amount = arguments.get("amount")

    try:
        amount = float(amount) if amount is not None else 0
    except (ValueError, TypeError):
        return {"error": "Invalid amount"}

    # Get asset_type (optional parameter with reasonable default)
    asset_type = arguments.get("asset_type") or "stock"
    asset_type = asset_type.lower()

    # Get user_tier (optional parameter with reasonable default)
    user_tier = arguments.get("user_tier") or "standard"
    user_tier = user_tier.lower()

    # Fee Logic
    rate = 0.0
    min_fee = 0.0

    if asset_type == "stock":
        rate = 0.001 # 0.1%
        min_fee = 5.00
    elif asset_type == "crypto":
        rate = 0.01 # 1.0%
        min_fee = 2.00
    elif asset_type == "forex":
        rate = 0.005 # 0.5%
        min_fee = 10.00
    
    # VIP Discount
    if user_tier == "vip":
        rate *= 0.5
        min_fee = 0.0

    calculated_fee = amount * rate
    fee = max(calculated_fee, min_fee)
    total_cost = amount + fee

    # Report effective rate so fee_rate and fee_amount are consistent
    effective_rate = (fee / amount) if amount > 0 else rate

    return {
        "amount": amount,
        "fee_rate": f"{effective_rate*100:.2f}%",
        "fee_amount": round(fee, 2),
        "total_cost": round(total_cost, 2),
        "currency": "USD"
    }