"""
get_light_status Tool Plugin
Specialized version of get_iot_device_status
"""

TOOL_NAME = "get_light_status"

CONSTRAINTS = {
    "light_id": ["light_living", "light_bedroom"]
}

# Mock Data (Hardcoded for standalone execution)
LIGHT_STATES = {
    "light_living": {"power_state": "off", "brightness": 0, "color": "white"},
    "light_bedroom": {"power_state": "on", "brightness": 50, "color": "white"}
}

def execute(arguments, context) -> dict:
    # 只验证真正必填的参数（required: ["light_id"]）
    light_id = arguments.get("light_id")

    if not light_id:
        return {"error": "light_id is required"}

    # Semantic Check: Is this actually a light?
    if "light" not in light_id:
        return {
            "error": f"Device '{light_id}' does not appear to be a light. Please use 'get_iot_device_status' for generic devices."
        }

    state = LIGHT_STATES.get(light_id)
    if not state:
        return {"error": "Light not found"}

    # 复制状态以避免修改原始数据
    current_state = state.copy()

    # 根据 context.history 中的灯光控制操作更新状态
    if hasattr(context, 'history'):
        for record in context.history:
            if record.output.get("device_id") == light_id or record.arguments.get("light_id") == light_id:
                if record.tool_name == "set_light_state" and "error" not in record.output:
                    current_state["power_state"] = record.output.get("changes", {}).get("power_state")
                elif record.tool_name == "set_light_brightness" and "error" not in record.output:
                    current_state["brightness"] = record.output.get("brightness")

    result = {"device_id": light_id}
    result.update(current_state)

    return result