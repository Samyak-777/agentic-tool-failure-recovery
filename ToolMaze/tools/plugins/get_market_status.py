"""
get_market_status Tool Plugin
Function: Check if exchange is open
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_market_status"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_market_status",
    "get_market_status_alpha",
    "get_market_status_polygon",
    "get_market_status_iex"
]

CONSTRAINTS = {
    "exchange": ["NYSE", "NASDAQ", "LSE", "HKEX", "CRYPTO"]
}

# Hardcoded Market Status
# Assume current simulation time is a weekday during US trading hours
MARKET_STATUS = {
    "NYSE": {"is_open": True, "session": "regular", "next_close": "16:00 EST"},
    "NASDAQ": {"is_open": True, "session": "regular", "next_close": "16:00 EST"},
    "LSE": {"is_open": False, "session": "closed", "next_open": "08:00 GMT"}, # London
    "HKEX": {"is_open": False, "session": "closed", "next_open": "09:30 HKT"}, # Hong Kong
    "CRYPTO": {"is_open": True, "session": "24/7", "next_close": "N/A"},
}

DEFAULT_STATUS = {"is_open": False, "session": "unknown", "reason": "Exchange not tracked"}

def execute(arguments, context) -> dict:
    """获取市场状态"""
    # Get exchange (optional parameter with reasonable default)
    exchange = arguments.get("exchange") or "US"
    if exchange:
        exchange = exchange.upper()

    # 检查是否已查询过该交易所状态
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
        "details": status
    }