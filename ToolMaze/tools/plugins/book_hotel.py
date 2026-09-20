"""
book_hotel Tool Plugin

Function: Book a hotel room (simulated)
Category: Action
Domain: Travel
"""

TOOL_NAME = "book_hotel"

CONSTRAINTS = {
    "room_type": ["standard", "deluxe", "suite"]
}

def execute(arguments, context) -> dict:
    """
    Book hotel room (simulation)

    Args:
        arguments: Tool parameters
            - hotel_name (str): Hotel name
            - check_in_date (str): Check-in date (YYYY-MM-DD)
            - check_out_date (str): Check-out date (YYYY-MM-DD)
            - guest_name (str): Guest name
            - room_type (str, optional): Room type (standard, deluxe, suite)

    Returns:
        dict: Dictionary containing booking status
    """
    hotel_name = arguments.get("hotel_name")

    check_in_date = arguments.get("check_in_date")

    check_out_date = arguments.get("check_out_date")

    guest_name = arguments.get("guest_name")

    room_type = arguments.get("room_type") or "standard"
    if room_type:
        room_type = room_type.lower()

    # 验证必填参数
    if not hotel_name:
        return {
            "error": "Hotel name is required"
        }

    if not check_in_date:
        return {
            "error": "Check-in date is required"
        }

    if not check_out_date:
        return {
            "error": "Check-out date is required"
        }

    if not guest_name:
        return {
            "error": "Guest name is required"
        }

    # Validate and normalize room type
    if room_type not in ["standard", "deluxe", "suite"]:
        return {
            "error": f"Invalid room type: {room_type}. Must be standard, deluxe, or suite"
        }

    booking_id = "HOTEL8D99FB"
    confirmation_code = "891392"

    return {
        "message": "Hotel booked successfully",
        "booking_id": booking_id,
        "confirmation_code": confirmation_code,
        "hotel_name": hotel_name,
        "guest_name": guest_name,
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "room_type": room_type,
        "status": "confirmed"
    }
