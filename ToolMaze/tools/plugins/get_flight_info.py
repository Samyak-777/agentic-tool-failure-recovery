"""
get_flight_info Tool Plugin

Function: Get flight status and details by flight number
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_flight_info"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_flight_info",
    "get_flight_info_aviationstack",
    "get_flight_info_flightaware",
    "get_flight_info_flightradar"
]

# Deterministic mapping of flight_number -> flight info
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
DEFAULT = {
    "flight_number": "Unknown",
    "airline": "Unknown",
    "departure": "Unknown",
    "arrival": "Unknown",
    "departure_time": "N/A",
    "arrival_time": "N/A",
    "status": "Not Found",
    "gate": "N/A"
}

CONSTRAINTS = {
    "flight_number": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """
    Get flight information by flight number

    Args:
        arguments: Tool parameters
            - flight_number (str): Flight number, e.g., CA1234, MU5678
        context: ExecutionContext，可访问前序工具输出

    Returns:
        dict: Dictionary containing flight information
    """
    flight_number = (arguments.get("flight_number") or "").upper()

    # 检查是否已查询过该航班
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"flight_number": flight_number}
        )
        if existing:
            return existing

    return dict(CASES.get(flight_number, DEFAULT))
