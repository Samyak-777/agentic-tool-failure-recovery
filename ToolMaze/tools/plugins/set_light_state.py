"""
set_light_state Tool Plugin

Function: Control smart light settings
Category: Action
Domain: IoT
"""

TOOL_NAME = "set_light_state"

CONSTRAINTS = {
    "device_id": ["light_living", "light_bedroom"],
    "state": ["on", "off"]
}

# Valid IDs for validation
VALID_LIGHTS = ["light_living", "light_bedroom"]

def execute(arguments, context) -> dict:
    # 优先从 context 获取参数
    device_id = arguments.get("device_id")

    state = arguments.get("state") or "on"

    brightness = arguments.get("brightness")
    if brightness is None:
        brightness = 80

    color = arguments.get("color") or 'white'

    # 1. Device ID Validation
    if device_id not in VALID_LIGHTS:
        return {
            "error": f"Device '{device_id}' is not a valid smart light or does not exist."
        }

    # 2. Parameter Logic Validation
    updated_attributes = {}
    
    if state:
        if state.lower() not in ["on", "off"]:
            return {"error": "Invalid state. Use 'on' or 'off'."}
        updated_attributes["power_state"] = state.lower()

    if brightness is not None:
        try:
            b_val = int(brightness)
            if not (0 <= b_val <= 100):
                 return {"error": "Brightness must be between 0 and 100."}
            updated_attributes["brightness"] = b_val
        except ValueError:
            return {"error": "Brightness must be an integer."}

    if color:
        updated_attributes["color"] = str(color)

    return {
        "device_id": device_id,
        "operation": "control_smart_light",
        "changes": updated_attributes,
        "status": "executed"
    }
