"""
set_light_brightness Tool Plugin
Parameter variant version of control_smart_light
"""

TOOL_NAME = "set_light_brightness"

CONSTRAINTS = {
    "light_id": ["light_living", "light_bedroom"]
}

# Valid IDs for validation (Hardcoded for simulation)
VALID_LIGHTS = ["light_living", "light_bedroom"]

def execute(arguments, context) -> dict:
    # 只验证真正必填的参数（required: ["light_id", "brightness"]）
    light_id = arguments.get("light_id")

    brightness = arguments.get("brightness")

    if not light_id:
        return {"error": "light_id is required"}

    if brightness is None:
        return {"error": "brightness is required"}

    # 兼容旧的 target_device 和 level 参数
    device_id = light_id
    level = brightness

    return {
        "device": device_id,
        "set_level": level,
        "actual_brightness": level,
        "message": "Brightness adjusted"
    }