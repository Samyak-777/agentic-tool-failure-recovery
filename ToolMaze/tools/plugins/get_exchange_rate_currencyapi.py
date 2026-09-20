TOOL_NAME = "get_exchange_rate_currencyapi"

from tools.plugins import get_exchange_rate_fixer as ge

# 可替换工具组
ALTERNATIVE_TOOLS = ge.ALTERNATIVE_TOOLS

# CurrencyAPI uses the same data structure as Fixer
CASES = ge.CASES

CONSTRAINTS = {
    "from_currency": ["USD", "EUR", "JPY", "GBP", "CNY", "BTC"],
    "to_currency": ["USD", "EUR", "JPY", "GBP", "CNY", "BTC"]
}


def execute(arguments, context):
    """获取汇率"""
    from_cur = (arguments.get("from_currency") or "USD").upper()
    to_cur = (arguments.get("to_currency") or "USD").upper()

    # 检查是否已查询过该汇率对
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"from_currency": from_cur, "to_currency": to_cur}
        )
        if existing:
            return existing

    if from_cur == to_cur:
        return {"rate": 1.0}
    rate = CASES.get((from_cur, to_cur), 1.0)
    return {"rate": rate}
