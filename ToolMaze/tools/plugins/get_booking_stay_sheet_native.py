"""
get_booking_stay_sheet_native Tool Plugin

Function: Retrieve a Booking-native stay sheet
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_booking_stay_sheet_native"

from tools.plugins import get_hotel_info_booking as ghib


def execute(arguments, context) -> dict:
    hotel = ghib.execute(arguments, context)
    if "error" in hotel:
        return hotel

    hotel_name = hotel.get("hotel_name") or arguments.get("hotel_name") or "Hilton Tokyo"
    return {
        "stay_sheet_id": f"booking_{hotel_name.lower().replace(' ', '_')}",
        "property_name": hotel_name,
        "city_label": hotel.get("location") or "Unknown",
        "nightly_usd": hotel.get("price_per_night", 0),
        "availability_state": hotel.get("availability") or "Unknown",
        "rating_value": hotel.get("rating", 0.0),
    }
