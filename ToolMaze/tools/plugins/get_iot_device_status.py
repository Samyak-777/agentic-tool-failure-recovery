"""
get_iot_device_status Tool Plugin

Function: Get real-time status of a specific IoT device
Category: Source
Domain: IoT
"""

TOOL_NAME = "get_iot_device_status"

CONSTRAINTS = {
    "device_id": ["lock_main", "lock_bedroom", "light_living", "light_bedroom",
                  "ac_living", "ac_bedroom", "tv_living", "sensor_bedroom_window", "tv_bedroom"]
}

# Mock State Database
# Pre-defined states for IoT devices
DEVICE_STATES = {
    "lock_main": {"online_status": "online", "power_state": "on", "locked": True, "battery_level": 85},
    "lock_bedroom": {"online_status": "online", "power_state": "on", "locked": False, "battery_level": 90},

    "light_living": {"power_state": "off", "brightness": 0, "color": "white"},
    "light_bedroom": {"power_state": "on", "brightness": 50, "color": "white"},
    
    "ac_living": {"online_status": "online", "power_state": "on", "temperature": 24.0, "mode": "cool"},
    "ac_bedroom": {"online_status": "online", "power_state": "off", "temperature": 26.0, "mode": "off"},

    "tv_living": {"online_status": "online", "power_state": "off", "volume": 20},
    "tv_bedroom": {"online_status": "online", "power_state": "off", "volume": 20},

    "sensor_bedroom_window": {"online_status": "online", "state": "closed", "battery_level": 98},
}

def execute(arguments, context) -> dict:
    """
    Get device status

    Args:
        arguments:
            - device_id (str): Unique ID

    Returns:
        dict: Device status details
    """
    # 只验证真正必填的参数（required: ["device_id"]）
    device_id = arguments.get("device_id")

    if not device_id:
        return {"error": "device_id is required"}

    # 获取初始状态
    state = DEVICE_STATES.get(device_id)

    if not state:
        return {
            "error": "Device not found",
            "device_id": device_id,
            "online_status": "unknown"
        }

    # 复制状态以避免修改原始数据
    current_state = state.copy()

    # 根据 context.history 中的设备控制操作更新状态
    if hasattr(context, 'history'):
        for record in context.history:
            # 检查各种设备控制工具
            if record.output.get("device_id") == device_id or record.arguments.get("device_id") == device_id:
                if record.tool_name == "set_power_state" and "error" not in record.output:
                    current_state["power_state"] = record.output.get("power_state")
                elif record.tool_name == "set_light_state" and "error" not in record.output:
                    current_state["power_state"] = record.output.get("changes", {}).get("power_state")
                elif record.tool_name == "set_light_brightness" and "error" not in record.output:
                    current_state["brightness"] = record.output.get("brightness")
                elif record.tool_name == "set_lock_state" and "error" not in record.output:
                    new_state = record.output.get("new_state")
                    if new_state is not None:
                        current_state["locked"] = (new_state == "locked")
                elif record.tool_name == "adjust_temperature" and "error" not in record.output:
                    current_state["temperature"] = record.output.get("temperature")

    result = {"device_id": device_id}
    result.update(current_state)

    return result