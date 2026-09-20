TOOL_NAME = "get_stock_yahoo_finance"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_stock_yahoo_finance",
    "get_stock_alpha_vantage",
    "get_stock_finnhub"
]

# Deterministic mapping of ticker -> price (USD)
CASES = {
    "AAPL": {"price_usd": 170.25, "currency": "USD"},
    "GOOGL": {"price_usd": 138.40, "currency": "USD"},
    "TSLA": {"price_usd": 245.10, "currency": "USD"},
    "MSFT": {"price_usd": 330.75, "currency": "USD"},
    "AMZN": {"price_usd": 140.60, "currency": "USD"},
}
DEFAULT = {"price_usd": 0.0, "currency": "USD"}

CONSTRAINTS = {
    "ticker": list(CASES.keys())
}


def execute(arguments, context):
    """获取股票价格"""
    ticker = (arguments.get("ticker") or "").upper()

    # 检查是否已查询过该股票
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"ticker": ticker}
        )
        if existing:
            return existing

    return dict(CASES.get(ticker, DEFAULT))

