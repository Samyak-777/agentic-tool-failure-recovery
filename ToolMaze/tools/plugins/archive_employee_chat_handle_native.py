"""
archive_employee_chat_handle_native Tool Plugin

Function: Archive an employee-chat native handle
Category: Action
Domain: Office
"""

TOOL_NAME = "archive_employee_chat_handle_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    chat_handle = arguments.get("chat_handle") or {}
    if not isinstance(chat_handle, dict):
        return {"error": "chat_handle must be an object"}

    result = cdaafd.execute(
        {
            "data": chat_handle,
            "title": arguments.get("title") or "Employee Chat Handle",
            "tags": ["contact", "chat", "native"],
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "archived",
        "strategy": "employee_handle_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "contact_ref": chat_handle.get("employee_code") or "emp_handle",
    }
