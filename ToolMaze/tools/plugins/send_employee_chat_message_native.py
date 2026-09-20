"""
send_employee_chat_message_native Tool Plugin

Function: Send an instant message using an employee-chat handle
Category: Action
Domain: Office
"""

TOOL_NAME = "send_employee_chat_message_native"

from tools.plugins import send_instant_message as sim


def execute(arguments, context) -> dict:
    employee_handle = arguments.get("employee_handle") or {}
    if not isinstance(employee_handle, dict):
        return {"error": "employee_handle must be an object"}

    user_id = employee_handle.get("chat_user_id") or "u_alice"
    message = arguments.get("message") or "Hello"

    result = sim.execute(
        {
            "user_id": user_id,
            "message": message,
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": result.get("status", "sent"),
        "strategy": "employee_chat_native",
        "channel": "im",
        "target": user_id,
        "reference_id": employee_handle.get("employee_code") or "emp_placeholder",
        "user_id": user_id,
    }
