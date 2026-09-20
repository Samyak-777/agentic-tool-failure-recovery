"""
get_polygon_market_board_native Tool Plugin

Function: Retrieve a Polygon-native market board
Category: Source
Domain: Financial
"""

TOOL_NAME = "get_polygon_market_board_native"

from tools.plugins import get_market_status_polygon as gmsp


def execute(arguments, context) -> dict:
    market = gmsp.execute(arguments, context)
    if "error" in market:
        return market

    exchange = market.get("exchange") or arguments.get("exchange") or "NYSE"
    details = market.get("details") or {}
    return {
        "polygon_board_id": f"polygon_{exchange.lower()}",
        "market_code": exchange,
        "board_live": market.get("is_open"),
        "session_band": market.get("session"),
        "next_mark": details.get("next_close") or details.get("next_open") or details.get("reason") or "N/A",
    }
