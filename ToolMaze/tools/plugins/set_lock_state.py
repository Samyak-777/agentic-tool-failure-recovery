"""
set_lock_state Tool Plugin

Function: Lock or unlock a smart door lock
Category: Action
Domain: IoT
"""

TOOL_NAME = "set_lock_state"

CONSTRAINTS = {
    "lock_id": ["lock_main", "lock_bedroom"],
    "state": ["lock", "unlock"]
}

VALID_LOCKS = ["lock_main", "lock_bedroom"]
CORRECT_PIN = "2026"

def execute(arguments, context) -> dict:
    # 使用默认值（与 YAML 定义一致）
    pin_code = arguments.get("pin_code", CORRECT_PIN)

    # 只验证真正必填的参数（required: ["lock_id", "state"]）
    lock_id = arguments.get("lock_id")

    state = arguments.get("state")

    if not lock_id:
        return {"error": "lock_id is required"}

    if not state:
        return {"error": "state is required"}

    # 兼容旧的 device_id 和 action 参数
    device_id = lock_id
    action = state

    if device_id not in VALID_LOCKS:
        return {"error": "Invalid lock device ID."}

    if action not in ["lock", "unlock"]:
        return {"error": "Action must be 'lock' or 'unlock'."}

    # Security Check Logic
    if action == "unlock":
        if not pin_code:
            return {
                "error": "PIN code is required to unlock.",
                "error_code": "AUTH_REQUIRED"
            }
        
        if pin_code != CORRECT_PIN:
            return {
                "error": "Incorrect PIN code.",
                "error_code": "AUTH_FAILED"
            }

    return {
        "device_id": device_id,
        "new_state": "unlocked" if action == "unlock" else "locked"
    }