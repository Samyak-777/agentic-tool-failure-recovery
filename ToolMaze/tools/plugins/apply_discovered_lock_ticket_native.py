"""
apply_discovered_lock_ticket_native Tool Plugin

Function: Apply a lock control using a discovered-lock native ticket
Category: Action
Domain: IoT
"""

TOOL_NAME = "apply_discovered_lock_ticket_native"

from tools.plugins import apply_lock_state as als


def execute(arguments, context) -> dict:
    lock_ticket = arguments.get("lock_ticket") or {}
    if not isinstance(lock_ticket, dict):
        return {"error": "lock_ticket must be an object"}

    result = als.execute(
        {
            "lock_id": lock_ticket.get("lock_device_id"),
            "state": arguments.get("state"),
            "pin_code": arguments.get("pin_code") or "2026",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": result.get("status", "executed"),
        "strategy": "discovered_lock_control_native",
        "device_id": result.get("device_id"),
        "new_state": result.get("new_state"),
        "control_ref": lock_ticket.get("lock_ticket_id") or "discovered_lock_ticket",
    }
