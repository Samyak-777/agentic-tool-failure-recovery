"""
build_device_restart_request Tool Plugin

Function: Build a normalized device restart request from current device status
Category: Processor
Domain: IoT
"""

TOOL_NAME = "build_device_restart_request"


def execute(arguments, context) -> dict:
    del context

    device_status = arguments.get("device_status")
    if not isinstance(device_status, dict):
        return {"error": "device_status must be an object"}

    device_id = device_status.get("device_id")
    if not device_id:
        return {"error": "device_status.device_id is required"}

    return {
        "device_id": device_id,
        "restart_reason": "status_driven_recovery",
    }
