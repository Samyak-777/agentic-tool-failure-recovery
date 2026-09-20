TOOL_NAME = "get_market_status_polygon"

from tools.plugins import get_market_status as gm

ALTERNATIVE_TOOLS = gm.ALTERNATIVE_TOOLS
CONSTRAINTS = gm.CONSTRAINTS
MARKET_STATUS = gm.MARKET_STATUS
DEFAULT_STATUS = gm.DEFAULT_STATUS


def execute(arguments, context) -> dict:
    """获取市场状态（Polygon）"""
    exchange = (arguments.get("exchange") or "US").upper()

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"exchange": exchange}
        )
        if existing:
            return existing

    status = MARKET_STATUS.get(exchange, DEFAULT_STATUS)
    return {
        "exchange": exchange,
        "is_open": status["is_open"],
        "session": status["session"],
        "details": status,
    }
