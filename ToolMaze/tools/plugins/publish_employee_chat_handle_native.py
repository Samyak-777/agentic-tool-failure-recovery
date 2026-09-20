"""
publish_employee_chat_handle_native Tool Plugin

Function: Publish an employee-chat native handle summary
Category: Action
Domain: Office
"""

TOOL_NAME = "publish_employee_chat_handle_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    chat_handle = arguments.get("chat_handle") or {}
    if not isinstance(chat_handle, dict):
        return {"error": "chat_handle must be an object"}

    legal_name = chat_handle.get("legal_name") or "Colleague"
    chat_user_id = chat_handle.get("chat_user_id") or "u_unknown"
    team = chat_handle.get("team") or "unknown"
    message = f"Employee chat {legal_name}: {chat_user_id} ({team})"
    user_id = arguments.get("user_id") or "default_user"

    result = pa.execute(
        {
            "message": message,
            "user_id": user_id,
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "published",
        "strategy": "employee_handle_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "contact_ref": chat_handle.get("employee_code") or "emp_handle",
        "content": result.get("content", message),
    }
