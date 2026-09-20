"""
update_device_config Tool Plugin

Function: Adjust non-power properties for IoT devices
Category: Action
Domain: IoT
"""

TOOL_NAME = "update_device_config"

# Property capabilities per device (based on DEVICE_STATES structure)
DEVICE_PROPERTIES = {
    "light_living": ["brightness", "color"],
    "light_bedroom": ["brightness", "color"],  # Though offline, we define capabilities
    "ac_living": ["temperature"],
    "ac_bedroom": ["temperature"],
    "tv_living": ["volume"],
    "tv_bedroom": ["volume"]
}

# Property validation rules
PROPERTY_RULES = {
    "brightness": {
        "type": int,
        "min": 0,
        "max": 100,
        "error": "Brightness must be integer between 0-100"
    },
    "temperature": {
        "type": (int, float),
        "min": 16.0,
        "max": 30.0,
        "error": "Temperature must be between 16-30°C"
    },
    "volume": {
        "type": int,
        "min": 0,
        "max": 100,
        "error": "Volume must be integer between 0-100"
    },
    # Color has no range validation, only type check
    "color": {
        "type": str,
        "error": "Color must be a string (e.g., 'red', '#FF0000')"
    }
}

# Simulated offline devices
OFFLINE_DEVICES = ["light_bedroom"]

CONSTRAINTS = {
    "device_id": list(DEVICE_PROPERTIES.keys()),
    "property": list(PROPERTY_RULES.keys())
}

def execute(arguments, context) -> dict:
    device_id = arguments.get("device_id") or "light_bedroom"

    prop = arguments.get("property") or "brightness"
    prop = prop.lower()

    value = arguments.get("value")

    # 1. Device validation
    if device_id not in DEVICE_PROPERTIES:
        return {
            "error": f"Device '{device_id}' does not support property adjustment. Valid devices: {', '.join(DEVICE_PROPERTIES.keys())}"
        }

    # 2. Offline check
    if device_id in OFFLINE_DEVICES:
        return {
            "error": f"Device '{device_id}' is offline. Cannot adjust properties."
        }

    # 3. Property validation
    if prop not in DEVICE_PROPERTIES[device_id]:
        return {
            "error": f"Property '{prop}' not supported for {device_id}. Supported properties: {', '.join(DEVICE_PROPERTIES[device_id])}"
        }

    # 4. Value validation
    rules = PROPERTY_RULES[prop]
    value_type = rules["type"]
    
    # Type check
    if not isinstance(value, value_type):
        # Special handling for temperature (accept int as float)
        if prop == "temperature" and isinstance(value, int):
            value = float(value)
        else:
            return {
                "error": f"{rules['error']} (got {type(value).__name__})"
            }
    
    # Range check (for numeric properties)
    if prop in ["brightness", "volume", "temperature"]:
        min_val = rules["min"]
        max_val = rules["max"]
        num_value = float(value) if prop == "temperature" else int(value)
        
        if not (min_val <= num_value <= max_val):
            return {
                "error": f"{rules['error']}. Current value: {num_value}"
            }

    return {
        "device_id": device_id,
        "operation": "adjust_device_property",
        "changes": {prop: value},
        "status": "executed"
    }