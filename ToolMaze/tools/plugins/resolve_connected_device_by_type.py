"""
resolve_connected_device_by_type Tool Plugin

Function: Resolve the first connected device ID that matches a requested IoT type
Category: Processor
Domain: IoT
"""

TOOL_NAME = "resolve_connected_device_by_type"

PREFIX_BY_TYPE = {
    "smart_light": "light_",
    "thermostat": "ac_",
    "media_player": "tv_",
    "smart_lock": "lock_",
}


def execute(arguments, context) -> dict:
    del context

    connected_data = arguments.get("connected_data")
    device_type = (arguments.get("device_type") or "").lower()

    if not isinstance(connected_data, dict):
        return {"error": "connected_data must be an object"}
    if device_type not in PREFIX_BY_TYPE:
        return {"error": f"Unsupported device_type '{device_type}'"}

    prefix = PREFIX_BY_TYPE[device_type]
    items = connected_data.get("items") or []
    for device_id in items:
        if isinstance(device_id, str) and device_id.startswith(prefix):
            return {
                "device_id": device_id,
                "device_type": device_type,
                "area": connected_data.get("area_name"),
                "selection_reason": f"resolved_first_{device_type}",
            }

    return {
        "error": f"No connected device of type '{device_type}' found.",
        "device_type": device_type,
        "area": connected_data.get("area_name"),
    }
