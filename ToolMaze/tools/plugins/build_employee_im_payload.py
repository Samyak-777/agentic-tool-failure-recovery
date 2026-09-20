"""
build_employee_im_payload Tool Plugin

Function: Build a normalized instant-message payload from resolved employee information
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_employee_im_payload"


def execute(arguments, context) -> dict:
    del context

    employee_data = arguments.get("employee_data")
    if not isinstance(employee_data, dict):
        return {"error": "employee_data must be an object"}

    user_id = employee_data.get("user_id")
    if not user_id:
        return {"error": "employee_data.user_id is required"}

    message = arguments.get("message")
    if not message:
        return {"error": "message is required"}

    return {
        "user_id": user_id,
        "message": message,
    }
