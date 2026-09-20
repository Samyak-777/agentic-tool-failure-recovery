"""
get_employee_chat_handle_native Tool Plugin

Function: Retrieve an employee-chat handle using an HR-native roster lookup
Category: Source
Domain: Office
"""

TOOL_NAME = "get_employee_chat_handle_native"

from tools.plugins import get_employee_id as gei

CONSTRAINTS = gei.CONSTRAINTS


def execute(arguments, context) -> dict:
    name = arguments.get("name")
    if not name:
        return {"error": "name is required"}

    employee = gei.execute({"name": name}, context)
    if "error" in employee or employee.get("found") is False:
        return employee

    user_id = employee.get("user_id") or "u_unknown"
    code_suffix = user_id[2:] if user_id.startswith("u_") else user_id
    return {
        "employee_code": f"emp_{code_suffix}",
        "chat_user_id": user_id,
        "team": employee.get("department") or "unknown",
        "legal_name": str(name).title(),
    }
