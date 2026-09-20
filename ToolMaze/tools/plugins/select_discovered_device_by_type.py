"""
select_discovered_device_by_type Tool Plugin

Function: Select the first discovered device that matches a requested IoT type
Category: Processor
Domain: IoT
"""

TOOL_NAME = "select_discovered_device_by_type"

VALID_TYPES = ["smart_light", "thermostat", "media_player", "smart_lock"]


def execute(arguments, context) -> dict:
    del context

    discovery_data = arguments.get("discovery_data")
    device_type = (arguments.get("device_type") or "").lower()

    if not isinstance(discovery_data, dict):
        return {"error": "discovery_data must be an object"}
    if device_type not in VALID_TYPES:
        return {"error": f"device_type must be one of {VALID_TYPES}"}

    devices = discovery_data.get("devices") or []
    for device in devices:
        if isinstance(device, dict) and device.get("type") == device_type:
            return {
                "device_id": device.get("device_id"),
                "device_type": device_type,
                "device_name": device.get("name"),
                "location": discovery_data.get("location"),
                "selection_reason": f"selected_first_{device_type}",
            }

    return {
        "error": f"No discovered device of type '{device_type}' found.",
        "device_type": device_type,
        "location": discovery_data.get("location"),
    }
