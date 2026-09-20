"""
get_crypto_price Tool Plugin

Function: Get current cryptocurrency price
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_crypto_price"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_crypto_price",
    "get_crypto_price_coingecko",
    "get_crypto_price_coinmarketcap",
    "get_crypto_price_kraken"
]

# Deterministic mapping of crypto symbol -> price
CASES = {
    "BTC": {
        "symbol": "BTC",
        "name": "Bitcoin",
        "price_usd": 42500.50,
        "change_24h": 2.35,
        "market_cap": 830000000000
    },
    "ETH": {
        "symbol": "ETH",
        "name": "Ethereum",
        "price_usd": 2250.75,
        "change_24h": -1.24,
        "market_cap": 270000000000
    },
    "BNB": {
        "symbol": "BNB",
        "name": "Binance Coin",
        "price_usd": 310.20,
        "change_24h": 0.85,
        "market_cap": 47000000000
    },
    "SOL": {
        "symbol": "SOL",
        "name": "Solana",
        "price_usd": 98.40,
        "change_24h": 3.67,
        "market_cap": 42000000000
    },
}
DEFAULT = {
    "symbol": "UNKNOWN",
    "name": "Unknown",
    "price_usd": 0.0,
    "change_24h": 0.0,
    "market_cap": 0
}

CONSTRAINTS = {
    "symbol": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """
    Get cryptocurrency price

    Args:
        arguments: Tool parameters
            - symbol (str): Cryptocurrency symbol (BTC, ETH, BNB, SOL)
        context: ExecutionContext，可访问前序工具输出

    Returns:
        dict: Dictionary containing cryptocurrency price information
    """
    symbol = (arguments.get("symbol") or "").upper()

    # 检查是否已查询过该加密货币
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"symbol": symbol}
        )
        if existing:
            return existing

    return dict(CASES.get(symbol, DEFAULT))
