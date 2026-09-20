"""
book_flight Tool Plugin

Function: Book a flight ticket (simulated)
Category: Action
Domain: Travel
"""

TOOL_NAME = "book_flight"
CASES = {
    "CA1234": {
        "flight_number": "CA1234",
        "airline": "Air China",
        "departure": "Beijing Capital Airport",
        "arrival": "Shanghai Pudong Airport",
        "departure_time": "08:30",
        "arrival_time": "11:00",
        "status": "On Time",
        "gate": "A12"
    },
    "MU5678": {
        "flight_number": "MU5678",
        "airline": "China Eastern",
        "departure": "Shanghai Hongqiao Airport",
        "arrival": "Guangzhou Baiyun Airport",
        "departure_time": "14:20",
        "arrival_time": "17:10",
        "status": "Delayed",
        "gate": "B06"
    },
    "CZ9012": {
        "flight_number": "CZ9012",
        "airline": "China Southern",
        "departure": "Guangzhou Baiyun Airport",
        "arrival": "Shenzhen Bao'an Airport",
        "departure_time": "10:15",
        "arrival_time": "11:05",
        "status": "Boarding",
        "gate": "C18"
    },
    "AA100": {
        "flight_number": "AA100",
        "airline": "American Airlines",
        "departure": "New York JFK",
        "arrival": "Los Angeles LAX",
        "departure_time": "09:00",
        "arrival_time": "12:30",
        "status": "On Time",
        "gate": "D24"
    },
}
CONSTRAINTS = {
    "flight_number": list(CASES.keys()),
    "seat_class": ["economy", "business", "first"],
    "class": ["economy", "business", "first"]
}

def execute(arguments, context) -> dict:
    """
    Book flight ticket (simulation)

    Args:
        arguments: Tool parameters
            - flight_number (str): Flight number
            - passenger_name (str): Passenger name
            - seat_class (str, optional): Seat class (economy, business, first)

    Returns:
        dict: Dictionary containing booking status
    """
    flight_number = arguments.get("flight_number")

    passenger_name = arguments.get("passenger_name")

    # Support both "class" and "seat_class" parameter names
    seat_class = arguments.get("class") or \
                 arguments.get("seat_class") or \
                 "economy"
    if seat_class:
        seat_class = seat_class.lower()

    # 验证必填参数
    if not flight_number:
        return {
            "error": "Flight number is required"
        }

    if not passenger_name:
        return {
            "error": "Passenger name is required"
        }

    # 验证前置条件：检查是否已查询过航班信息
    flight_info_queried = False
    if hasattr(context, 'history'):
        for record in context.history:
            if record.tool_name == "get_flight_info" and \
               record.arguments.get("flight_number") == flight_number:
                flight_info_queried = True
                break

    if not flight_info_queried:
        # 警告但不阻止预订（保持向后兼容）
        pass

    # Validate and normalize seat class
    if not seat_class:
        seat_class = "economy"
    elif seat_class not in ["economy", "business", "first"]:
        return {
            "error": f"Invalid seat class: {seat_class}. Must be economy, business, or first"
        }

    booking_id = "FLIGHT5A3B2C"
    confirmation_code = "D4E6F7"

    return {
        "message": "Flight booked successfully",
        "booking_id": booking_id,
        "confirmation_code": confirmation_code,
        "flight_number": flight_number,
        "passenger_name": passenger_name,
        "seat_class": seat_class,
        "status": "confirmed"
    }
