TOOL_NAME = "get_stock_alpha_vantage"

from tools.plugins import get_stock_yahoo_finance as gs

# 可替换工具组
ALTERNATIVE_TOOLS = gs.ALTERNATIVE_TOOLS

CASES = gs.CASES
DEFAULT = gs.DEFAULT

CONSTRAINTS = {
    "symbol": list(CASES.keys())
}


def execute(arguments, context):
    """获取股票价格"""
    symbol = (arguments.get("symbol") or "").upper()

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"symbol": symbol}
        )
        if existing:
            return existing

    return dict(CASES.get(symbol, DEFAULT))
