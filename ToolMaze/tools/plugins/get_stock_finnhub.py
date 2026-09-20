TOOL_NAME = "get_stock_finnhub"

from tools.plugins import get_stock_yahoo_finance as gs

# 可替换工具组
ALTERNATIVE_TOOLS = gs.ALTERNATIVE_TOOLS

CASES = gs.CASES
DEFAULT = gs.DEFAULT

CONSTRAINTS = {
    "ticker": list(CASES.keys())
}


def execute(arguments, context):
    """获取股票价格"""
    ticker = (arguments.get("ticker") or "").upper()

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"ticker": ticker}
        )
        if existing:
            return existing

    return dict(CASES.get(ticker, DEFAULT))
