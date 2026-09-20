TOOL_NAME = "get_exchange_rate_fixer"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_exchange_rate_fixer",
    "get_exchange_rate_currencyapi",
    "get_exchange_rate_exchangerate"
]

# 以 USD 为基准：1 USD = X 单位该货币
USD_BASE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "JPY": 150.0,
    "GBP": 0.78,
    "CNY": 7.20,
}

CONSTRAINTS = {
    "from_currency": list(USD_BASE_RATES.keys()),
    "to_currency": list(USD_BASE_RATES.keys()),
}

# 预计算所有货币对的汇率，供替代工具（currencyapi / exchangerate）直接引用
CASES = {
    (src, dst): round(USD_BASE_RATES[dst] / USD_BASE_RATES[src], 6)
    for src in USD_BASE_RATES
    for dst in USD_BASE_RATES
    if src != dst
}


def execute(arguments, context):
    """获取汇率，以 USD 为中转计算任意货币对"""
    from_cur = (arguments.get("from_currency") or arguments.get("from") or "USD").upper()
    to_cur = (arguments.get("to_currency") or arguments.get("to") or "USD").upper()

    # 检查是否已查询过该汇率对（任何替代工具）
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"from_currency": from_cur, "to_currency": to_cur}
        )
        if existing:
            return existing

    if from_cur == to_cur:
        return {"rate": 1.0}

    # 通过 USD 做中转：from -> USD -> to
    # rate(from→to) = USD_BASE_RATES[to] / USD_BASE_RATES[from]
    from_rate = USD_BASE_RATES.get(from_cur)
    to_rate = USD_BASE_RATES.get(to_cur)
    if from_rate is None or to_rate is None:
        return {"rate": 1.0}

    rate = round(to_rate / from_rate, 6)
    return {"rate": rate}

