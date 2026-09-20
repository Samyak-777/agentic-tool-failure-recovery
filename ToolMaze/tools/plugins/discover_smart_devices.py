"""
discover_smart_devices Tool Plugin

Function: Discover available IoT devices in a specific location
Category: Source
Domain: IoT
"""

TOOL_NAME = "discover_smart_devices"

CONSTRAINTS = {
    "location": ["living_room", "bedroom"]
}

# Mock Database: Device Layout
# Defines which devices are located in which room
LOCATION_MAP = {
    "living_room": [
        {"device_id": "lock_main", "name": "Main Door Lock", "type": "smart_lock"},
        {"device_id": "light_living", "name": "Living Room Main Light", "type": "smart_light"},
        {"device_id": "ac_living", "name": "Living Room AC", "type": "thermostat"},
        {"device_id": "tv_living", "name": "Living Room TV", "type": "media_player"},
    ],
    "bedroom": [
        {"device_id": "lock_bedroom", "name": "Bedroom Door Lock", "type": "smart_lock"},
        {"device_id": "light_bedroom", "name": "Bedroom Ambient Light", "type": "smart_light"},
        {"device_id": "ac_bedroom", "name": "Bedroom AC", "type": "thermostat"},
        {"device_id": "sensor_bedroom_window", "name": "Bedroom Window Sensor", "type": "sensor"},
        {"device_id": "tv_bedroom", "name": "Bedroom TV", "type": "media_player"},
    ]
}

def execute(arguments, context) -> dict:
    """
    Scan local devices by location

    Args:
        arguments:
            - location (str, optional): 'living_room', 'bedroom', etc. Default: 'all'

    Returns:
        dict: List of found devices
    """
    location = arguments.get("location")
    if not location:
        return {"error": "Missing required parameter: 'location'. Valid values: " + ", ".join(LOCATION_MAP.keys())}
    location = location.lower().replace(" ", "_")

    devices = LOCATION_MAP.get(location)

    if devices is None:
        # Robustness test: Handle unknown locations nicely
        return {
            "location": location,
            "device_count": 0,
            "devices": [],
            "message": f"No location named '{location}' found in home map."
        }

    return {
        "location": location,
        "device_count": len(devices),
        "devices": devices,
        "message": "Scan complete successfully."
    }