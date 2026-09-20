"""
build_contact_alert_payload Tool Plugin

Function: Build a normalized push-alert payload from contact information
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_contact_alert_payload"


def execute(arguments, context) -> dict:
    del context

    contact_data = arguments.get("contact_data")
    if not isinstance(contact_data, dict):
        return {"error": "contact_data must be an object"}

    user_id = contact_data.get("user_id")
    if not user_id:
        return {"error": "contact_data.user_id is required"}

    message = arguments.get("message")
    if not message:
        return {"error": "message is required"}

    return {
        "user_id": user_id,
        "recipient_name": contact_data.get("name", ""),
        "message": message,
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
