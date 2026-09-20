"""
get_aviationstack_gate_board_native Tool Plugin

Function: Retrieve an aviation-native gate board for a flight
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_aviationstack_gate_board_native"

from tools.plugins import get_flight_info_aviationstack as gfia

CONSTRAINTS = gfia.CONSTRAINTS


def execute(arguments, context) -> dict:
    flight_number = (arguments.get("flight_number") or "").upper()
    if not flight_number:
        return {"error": "flight_number is required"}

    flight = gfia.execute({"flight_number": flight_number}, context)
    if "error" in flight:
        return flight

    return {
        "board_ref": f"gate_{flight_number.lower()}",
        "flight_code": flight.get("flight_number", flight_number),
        "dep_airport": flight.get("departure"),
        "arr_airport": flight.get("arrival"),
        "gate_label": flight.get("gate"),
        "status_text": flight.get("status"),
    }
