"""
resolve_employee_record_identity Tool Plugin

Function: Resolve a normalized contact identity profile from an employee record
Category: Processor
Domain: Office
"""

TOOL_NAME = "resolve_employee_record_identity"


def execute(arguments, context) -> dict:
    del context

    employee_data = arguments.get("employee_data")
    if not isinstance(employee_data, dict):
        return {"error": "employee_data must be an object"}
    if employee_data.get("found") is False:
        return {"error": employee_data.get("error") or "employee_data did not resolve an employee"}

    user_id = employee_data.get("user_id")
    if not user_id:
        return {"error": "employee_data.user_id is required"}

    display_name = (arguments.get("name") or "").strip().title() or "Unknown"
    department = employee_data.get("department") or "unknown"

    return {
        "identity_method": "employee_record",
        "display_name": display_name,
        "user_id": user_id,
        "department": department,
        "contact_channel": "im",
        "contact_value": user_id,
    }
