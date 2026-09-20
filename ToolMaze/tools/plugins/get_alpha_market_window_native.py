"""
get_alpha_market_window_native Tool Plugin

Function: Retrieve an Alpha-native market window
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_alpha_market_window_native"

from tools.plugins import get_market_status_alpha as gmsa


def execute(arguments, context) -> dict:
    market = gmsa.execute(arguments, context)
    if "error" in market:
        return market

    exchange = market.get("exchange") or arguments.get("exchange") or "NYSE"
    details = market.get("details") or {}
    return {
        "alpha_window_id": f"alpha_{exchange.lower()}",
        "venue_code": exchange,
        "market_live": market.get("is_open"),
        "phase_label": market.get("session"),
        "transition_mark": details.get("next_close") or details.get("next_open") or details.get("reason") or "N/A",
    }
