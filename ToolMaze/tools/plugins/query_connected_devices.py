"""
query_connected_devices Tool Plugin
Alternative version of discover_smart_devices
"""

TOOL_NAME = "query_connected_devices"

CONSTRAINTS = {
    "area": ["living_room", "bedroom"]
}

# Mock Data
LOCATION_MAP = {
    "living_room": [
        {"device_id": "lock_main", "type": "smart_lock"},
        {"device_id": "light_living", "type": "smart_light"},
        {"device_id": "ac_living", "type": "thermostat"},
        {"device_id": "tv_living", "type": "media_player"},
    ],
    "bedroom": [
        {"device_id": "lock_bedroom", "type": "smart_lock"},
        {"device_id": "light_bedroom", "type": "smart_light"},
        {"device_id": "ac_bedroom", "type": "thermostat"},
        {"device_id": "sensor_bedroom_window", "type": "sensor"},
        {"device_id": "tv_bedroom", "type": "media_player"},
    ]
}

def execute(arguments, context) -> dict:
    device_type = arguments.get("device_type") or "all"

    area = arguments.get("area")
    if not area:
        return {"error": "Missing required parameter: 'area'. Valid values: " + ", ".join(LOCATION_MAP.keys())}

    area = area.lower().replace(" ", "_")

    devices = LOCATION_MAP.get(area)

    if devices is None:
        return {"found": False, "count": 0, "items": []}

    # Slightly different return format to test model adaptability
    return {
        "found": True,
        "area_name": area,
        "total_items": len(devices),
        "items": [d["device_id"] for d in devices]
    }