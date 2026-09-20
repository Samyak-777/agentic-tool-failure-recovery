"""
book_flight_with_status_check Tool Plugin

Function: Check flight status then book the flight in one step
Category: Action
Domain: Travel
"""

TOOL_NAME = "book_flight_with_status_check"

from tools.plugins import get_flight_info as gfi
from tools.plugins import book_flight as bf


def execute(arguments, context) -> dict:
    """先检查航班状态，再执行预订"""
    flight_number = arguments.get("flight_number")
    flight_info = gfi.execute({"flight_number": flight_number}, context)
    if "error" in flight_info:
        return flight_info

    if flight_info.get("status") == "Not Found":
        return {"error": f"Flight '{flight_number}' not found"}

    booking = bf.execute(
        {
            "flight_number": flight_number,
            "passenger_name": arguments.get("passenger_name"),
            "seat_class": arguments.get("seat_class") or arguments.get("class") or "economy",
        },
        context,
    )
    if "error" in booking:
        return booking

    booking["flight_status"] = flight_info.get("status")
    return booking
