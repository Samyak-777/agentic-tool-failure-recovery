"""
get_expedia_lodging_packet_native Tool Plugin

Function: Retrieve an Expedia-native lodging packet
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_expedia_lodging_packet_native"

from tools.plugins import get_hotel_info_expedia as ghie


def execute(arguments, context) -> dict:
    hotel = ghie.execute(arguments, context)
    if "error" in hotel:
        return hotel

    hotel_name = hotel.get("hotel_name") or arguments.get("hotel_name") or "Hilton Tokyo"
    return {
        "lodging_packet_id": f"expedia_{hotel_name.lower().replace(' ', '_')}",
        "hotel_label": hotel_name,
        "locale_name": hotel.get("location") or "Unknown",
        "rate_amount": hotel.get("price_per_night", 0),
        "inventory_state": hotel.get("availability") or "Unknown",
        "review_score": hotel.get("rating", 0.0),
    }
