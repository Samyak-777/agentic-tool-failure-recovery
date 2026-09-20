"""
book_available_hotel Tool Plugin

Function: Check hotel availability then book the hotel in one step
Category: Action
Domain: Travel
"""

TOOL_NAME = "book_available_hotel"

from tools.plugins import get_hotel_info as ghi
from tools.plugins import book_hotel as bh


def execute(arguments, context) -> dict:
    """先检查酒店可订状态，再完成预订"""
    hotel_name = arguments.get("hotel_name")
    hotel_info = ghi.execute({"hotel_name": hotel_name}, context)
    if "error" in hotel_info:
        return hotel_info

    availability = hotel_info.get("availability")
    if availability not in ("Available", "Limited"):
        return {
            "error": f"Hotel '{hotel_name}' is not available for booking",
            "availability": availability,
        }

    booking = bh.execute(
        {
            "hotel_name": hotel_name,
            "check_in_date": arguments.get("check_in_date"),
            "check_out_date": arguments.get("check_out_date") or "2026-01-03",
            "guest_name": arguments.get("guest_name"),
            "room_type": arguments.get("room_type") or "standard",
        },
        context,
    )
    if "error" in booking:
        return booking

    booking["availability"] = availability
    return booking
