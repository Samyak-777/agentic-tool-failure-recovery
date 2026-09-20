TOOL_NAME = "get_stock_price_and_convert"

# Simulated exchange rates
RATES = {"EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "CNY": 7.24, "CAD": 1.36, "AUD": 1.53}

# Simulated stock prices (USD)
PRICES = {"AAPL": 170.25, "GOOGL": 138.40, "MSFT": 330.75, "AMZN": 140.60, "TSLA": 245.10}


def execute(arguments, context):
    """获取股票价格并转换货币（组合工具）"""
    ticker = (arguments.get("ticker") or "").upper()
    target = (arguments.get("target_currency") or "USD").upper()

    price_usd = PRICES.get(ticker, 150.0)

    if target == "USD":
        return {"price": price_usd, "currency": "USD", "ticker": ticker}

    rate = RATES.get(target, 1.0)
    converted = round(price_usd * rate, 4)
    return {"price": converted, "currency": target, "ticker": ticker, "price_usd": price_usd, "rate": rate}
