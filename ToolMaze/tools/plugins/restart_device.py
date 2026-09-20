"""
restart_device Tool Plugin

Function: Restart a smart device (Recovery Tool)
Category: Action
Domain: IoT
"""

import time

TOOL_NAME = "restart_device"

CONSTRAINTS = {
    "device_id": ["lock_main", "lock_bedroom", "light_living", "light_bedroom",
                  "ac_living", "ac_bedroom", "tv_living", "sensor_bedroom_window", "tv_bedroom"]
}

def execute(arguments, context) -> dict:
    # 只验证真正必填的参数（required: ["device_id"]）
    device_id = arguments.get("device_id")

    if not device_id:
        return {"error": "device_id is required"}
    
    return {
        "device_id": device_id,
        "status": "rebooting",
        "message": "Device is restarting. Please wait 30 seconds before reconnecting.",
        "timestamp": "2026-02-22T23:04:54.104641"
    }
