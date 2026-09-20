"""
adjust_temperature Tool Plugin

Function: Control HVAC/Thermostat settings
Category: Action
Domain: IoT
"""

TOOL_NAME = "adjust_temperature"

CONSTRAINTS = {
    "device_id": ["ac_living", "ac_bedroom"],
    "mode": ["cool", "heat", "fan", "off", "auto", "eco"]
}

VALID_THERMOSTATS = ["ac_living", "ac_bedroom"]
VALID_MODES = ["cool", "heat", "fan", "off", "auto", "eco"]

def execute(arguments, context) -> dict:
    # 优先从 context 获取参数
    device_id = arguments.get("device_id") or "ac_living"

    temperature = arguments.get("temperature")

    mode = arguments.get("mode") or "eco"

    if device_id not in VALID_THERMOSTATS:
        return {"error": f"Device '{device_id}' is not a valid thermostat."}

    updated_attributes = {}

    # Mode validation
    if mode:
        if mode not in VALID_MODES:
            return {"error": f"Invalid mode '{mode}'. Allowed: {VALID_MODES}"}
        updated_attributes["mode"] = mode

    # Temperature validation (expanded range for flexibility)
    if temperature is not None:
        current_mode = mode if mode else "off"
        if current_mode in ["off", "fan"]:
             return {"error": f"Cannot set temperature in '{current_mode}' mode."}

        try:
            temp_val = float(temperature)
            if not (10.0 <= temp_val <= 35.0):
                return {"error": "Temperature must be between 10 and 35 degrees Celsius."}
            updated_attributes["temperature"] = temp_val
        except ValueError:
             return {"error": "Temperature must be a number."}

    return {
        "device_id": device_id,
        "changes": updated_attributes
    }