"""
build_hotel_booking_request Tool Plugin
Category: Processor
Domain: Travel
"""

TOOL_NAME = "build_hotel_booking_request"


def execute(arguments, context) -> dict:
    hotel_data = arguments.get("hotel_data") or {}
    if not isinstance(hotel_data, dict):
        return {"error": "hotel_data must be an object"}

    hotel_name = hotel_data.get("hotel_name")
    if not hotel_name or hotel_name == "Unknown":
        return {"error": "hotel_data does not contain a valid hotel_name"}

    guest_name = arguments.get("guest_name")
    check_in_date = arguments.get("check_in_date")
    check_out_date = arguments.get("check_out_date")
    room_type = (arguments.get("room_type") or "standard").lower()

    if not guest_name:
        return {"error": "guest_name is required"}
    if not check_in_date or not check_out_date:
        return {"error": "check_in_date and check_out_date are required"}

    return {
        "hotel_name": hotel_name,
        "guest_name": guest_name,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "room_type": room_type,
        "nightly_price": hotel_data.get("price_per_night", 0),
        "location": hotel_data.get("location", ""),
        "booking_ready": True,
    }
