"""
get_account_balance Tool Plugin
Function: Get current account balance
Category: Source
Domain: Financial
"""
import hashlib

TOOL_NAME = "get_account_balance"

ALTERNATIVE_TOOLS = [
    "get_account_balance",
    "get_account_balance_bank_api",
    "get_account_balance_broker_api",
    "get_account_balance_wallet_api"
]

CONSTRAINTS = {
    "account_type": ["checking", "savings", "investment"]
}

def execute(arguments, context) -> dict:
    # Get user_id (required parameter)
    user_id = arguments.get("user_id")

    if not user_id:
        return {"error": "user_id is required"}

    # Get account_type (optional parameter with reasonable default)
    account_type = arguments.get("account_type") or "investment"
    if account_type:
        account_type = account_type.lower()

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"user_id": user_id, "account_type": account_type}
        )
        if existing:
            return existing

    # 为user_id生成确定性的余额
    seed = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)
    balance = 10000 + (seed % 40000)
    data = {"balance": balance, "currency": "USD", "status": "active"}
    initial_balance = data["balance"]

    # 根据 context.history 中的交易记录调整余额
    if hasattr(context, 'history'):
        for record in context.history:
            # 处理买入订单（减少余额）- 没有 error 字段表示成功
            if record.tool_name == "place_buy_order" and "error" not in record.output:
                # 买入会减少账户余额
                cost = record.output.get("total_cost", 0)
                if cost:
                    initial_balance -= cost

            # 处理卖出订单（增加余额）- 没有 error 字段表示成功
            elif record.tool_name == "place_sell_order" and "error" not in record.output:
                # 卖出会增加账户余额
                pnl = record.output.get("realized_pnl", 0)
                if pnl:
                    initial_balance += pnl

    return {
        "user_id": user_id,
        "account_type": account_type,
        "balance": initial_balance,
        "currency": data["currency"],
        "status": data["status"]
    }