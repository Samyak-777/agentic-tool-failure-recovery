"""
apply_lock_state Tool Plugin

Function: Apply a normalized smart-lock request and return aligned metadata
Category: Action
Domain: IoT
"""

TOOL_NAME = "apply_lock_state"

from tools.plugins import set_lock_state as sls


def execute(arguments, context) -> dict:
    lock_id = arguments.get("lock_id")
    state = arguments.get("state")

    if not lock_id:
        return {"error": "lock_id is required"}
    if not state:
        return {"error": "state is required"}

    result = sls.execute(
        {
            "lock_id": lock_id,
            "state": state,
            "pin_code": arguments.get("pin_code") or "2026",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "device_id": result.get("device_id", lock_id),
        "new_state": result.get("new_state"),
        "status": "executed",
    }
