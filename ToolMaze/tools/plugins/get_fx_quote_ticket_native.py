"""
get_fx_quote_ticket_native Tool Plugin

Function: Retrieve an FX-adjusted quote ticket using a settlement-native source
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_fx_quote_ticket_native"

from tools.plugins import get_stock_price_and_convert as gspc

CONSTRAINTS = {
    "ticker": list(gspc.PRICES.keys()),
    "target_currency": ["USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"],
}


def execute(arguments, context) -> dict:
    del context

    ticker = (arguments.get("ticker") or "").upper()
    target_currency = (arguments.get("target_currency") or "USD").upper()
    if not ticker:
        return {"error": "ticker is required"}

    price_usd = gspc.PRICES.get(ticker, 150.0)
    if target_currency == "USD":
        local_last = price_usd
        fx_rate = 1.0
    else:
        fx_rate = gspc.RATES.get(target_currency, 1.0)
        local_last = round(price_usd * fx_rate, 4)

    return {
        "ticket_ref": f"fxt_{ticker.lower()}",
        "ticker_code": ticker,
        "local_last": local_last,
        "settlement_ccy": target_currency,
        "usd_reference": price_usd,
        "fx_rate": fx_rate,
    }
