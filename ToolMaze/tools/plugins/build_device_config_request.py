"""
build_device_config_request Tool Plugin

Function: Build a normalized generic device-config update request
Category: Processor
Domain: IoT
"""

TOOL_NAME = "build_device_config_request"


def execute(arguments, context) -> dict:
    del context

    device_ref = arguments.get("device_ref")
    if not isinstance(device_ref, dict):
        return {"error": "device_ref must be an object"}

    device_id = device_ref.get("device_id")
    if not device_id:
        return {"error": "device_ref.device_id is required"}

    prop = arguments.get("property")
    if not prop:
        return {"error": "property is required"}

    if "value" not in arguments:
        return {"error": "value is required"}

    return {
        "device_id": device_id,
        "property": prop,
        "value": arguments.get("value"),
    }
