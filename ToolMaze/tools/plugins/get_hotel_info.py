"""
get_hotel_price Tool Plugin

Function: Get all hotels' info
Category: Source
Domain: Travel
"""

TOOL_NAME = "get_hotel_info"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_hotel_info",
    "get_hotel_info_booking",
    "get_hotel_info_expedia"
]

# Deterministic mapping of hotel -> price info
CASES = {
    "Hilton Tokyo": {
        "hotel_name": "Hilton Tokyo",
        "location": "Tokyo, Japan",
        "price_per_night": 180,
        "currency": "USD",
        "rating": 4.5,
        "availability": "Available"
    },
    "Sheraton Paris": {
        "hotel_name": "Sheraton Paris",
        "location": "Paris, France",
        "price_per_night": 220,
        "currency": "USD",
        "rating": 4.3,
        "availability": "Available"
    },
    "Marriott New York": {
        "hotel_name": "Marriott New York",
        "location": "New York, USA",
        "price_per_night": 250,
        "currency": "USD",
        "rating": 4.6,
        "availability": "Limited"
    },
    "Shangri-La Beijing": {
        "hotel_name": "Shangri-La Beijing",
        "location": "Beijing, China",
        "price_per_night": 150,
        "currency": "USD",
        "rating": 4.7,
        "availability": "Available"
    },
}
DEFAULT = {
    "hotel_name": "Unknown",
    "location": "Unknown",
    "price_per_night": 0,
    "currency": "USD",
    "rating": 0.0,
    "availability": "Not Found"
}

CONSTRAINTS = {
    "hotel_name": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """
    Get all hotel information

    Args:
        arguments: Tool parameters
        context: ExecutionContext，可访问前序工具输出

    Returns:
        dict: Dictionary containing hotel pricing information
    """
    # Get hotel_name (optional parameter)
    hotel_name = arguments.get("hotel_name")

    # Check if this hotel has been queried before
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"hotel_name": hotel_name}
        )
        if existing:
            return existing

    # If hotel_name is not provided, return error
    if not hotel_name:
        return {"error": "hotel_name is required"}

    if hotel_name in CASES:
        return CASES[hotel_name]
    else:
        return DEFAULT
