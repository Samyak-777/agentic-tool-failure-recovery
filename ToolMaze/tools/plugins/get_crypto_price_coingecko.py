TOOL_NAME = "get_crypto_price_coingecko"

from tools.plugins import get_crypto_price as gc

ALTERNATIVE_TOOLS = gc.ALTERNATIVE_TOOLS
CASES = gc.CASES
DEFAULT = gc.DEFAULT

CONSTRAINTS = {
    "symbol": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """获取加密货币价格（CoinGecko）"""
    symbol = (arguments.get("symbol") or "").upper()

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"symbol": symbol}
        )
        if existing:
            return existing

    return dict(CASES.get(symbol, DEFAULT))
