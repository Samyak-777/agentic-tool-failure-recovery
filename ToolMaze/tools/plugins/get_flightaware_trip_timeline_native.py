"""
get_flightaware_trip_timeline_native Tool Plugin

Function: Retrieve a flightaware-native trip timeline for a flight
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_flightaware_trip_timeline_native"

from tools.plugins import get_flight_info_flightaware as gfif

CONSTRAINTS = gfif.CONSTRAINTS


def execute(arguments, context) -> dict:
    flight_number = (arguments.get("flight_number") or "").upper()
    if not flight_number:
        return {"error": "flight_number is required"}

    flight = gfif.execute({"flight_number": flight_number}, context)
    if "error" in flight:
        return flight

    return {
        "timeline_id": f"trip_{flight_number.lower()}",
        "flight_no": flight.get("flight_number", flight_number),
        "route_text": f"{flight.get('departure')} -> {flight.get('arrival')}",
        "latest_state": flight.get("status"),
        "checkpoint_gate": flight.get("gate"),
    }
