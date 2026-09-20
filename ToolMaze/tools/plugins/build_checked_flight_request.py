"""
build_checked_flight_request Tool Plugin
Category: Processor
Domain: Travel
"""

TOOL_NAME = "build_checked_flight_request"


def execute(arguments, context) -> dict:
    flight_data = arguments.get("flight_data") or {}
    passenger_name = arguments.get("passenger_name")
    seat_class = (arguments.get("seat_class") or "economy").lower()

    if not isinstance(flight_data, dict):
        return {"error": "flight_data must be an object"}
    if not passenger_name:
        return {"error": "passenger_name is required"}

    flight_number = flight_data.get("flight_number")
    if not flight_number or flight_number == "Unknown":
        return {"error": "flight_data does not contain a valid flight_number"}

    return {
        "flight_number": flight_number,
        "passenger_name": passenger_name,
        "seat_class": seat_class,
        "current_status": flight_data.get("status", "Unknown"),
        "booking_ready": True,
    }
