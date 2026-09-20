"""
set_power_state Tool Plugin

Function: Toggle power state for controllable devices
Category: Action
Domain: IoT
"""

TOOL_NAME = "set_power_state"
CONSTRAINTS = {
    "device_id": [
        "light_living", "light_bedroom",
        "ac_living", "ac_bedroom",
        "tv_living", "tv_bedroom"
    ],
    "state": ["on", "off"]
}
# Valid devices that support power toggling (based on DEVICE_STATES structure)
TOGGLEABLE_DEVICES = [
    "light_living", "light_bedroom", 
    "ac_living", "ac_bedroom",
    "tv_living", "tv_bedroom"
]

# Simulated offline devices (from DEVICE_STATES example)
OFFLINE_DEVICES = ["light_bedroom"]

def execute(arguments, context) -> dict:
    device_id = arguments.get("device_id")
    if not device_id:
        return {"error": "Missing required parameter: 'device_id'. Valid devices: " + ", ".join(TOGGLEABLE_DEVICES)}

    state = arguments.get("state") or "off"
    state = state.lower()

    # 1. Device validation
    if device_id not in TOGGLEABLE_DEVICES:
        return {
            "error": f"Device '{device_id}' does not support power toggling. Valid devices: {', '.join(TOGGLEABLE_DEVICES)}"
        }

    # 2. Offline check
    if device_id in OFFLINE_DEVICES:
        return {
            "error": f"Device '{device_id}' is offline. Cannot toggle power."
        }

    # 3. State validation
    if state not in ["on", "off"]:
        return {
            "error": f"Invalid power state '{state}'. Use 'on' or 'off'."
        }

    return {
        "device_id": device_id,
        "operation": "toggle_device_power",
        "changes": {"power_state": state},
        "status": "executed"
    }