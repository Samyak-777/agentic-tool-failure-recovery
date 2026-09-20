"""
apply_connected_lock_pass_native Tool Plugin

Function: Apply a lock control using a connected-lock native pass
Category: Action
Domain: IoT
"""

TOOL_NAME = "apply_connected_lock_pass_native"

from tools.plugins import apply_lock_state as als


def execute(arguments, context) -> dict:
    lock_pass = arguments.get("lock_pass") or {}
    if not isinstance(lock_pass, dict):
        return {"error": "lock_pass must be an object"}

    result = als.execute(
        {
            "lock_id": lock_pass.get("lock_device_id"),
            "state": arguments.get("state"),
            "pin_code": arguments.get("pin_code") or "2026",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": result.get("status", "executed"),
        "strategy": "connected_lock_control_native",
        "device_id": result.get("device_id"),
        "new_state": result.get("new_state"),
        "control_ref": lock_pass.get("lock_pass_ref") or "connected_lock_pass",
    }
