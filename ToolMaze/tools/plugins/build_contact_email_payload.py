"""
build_contact_email_payload Tool Plugin

Function: Build a normalized email payload from resolved contact information
Category: Processor
Domain: Office
"""

TOOL_NAME = "build_contact_email_payload"


def execute(arguments, context) -> dict:
    del context

    contact_data = arguments.get("contact_data")
    if not isinstance(contact_data, dict):
        return {"error": "contact_data must be an object"}

    email = contact_data.get("email")
    if not email:
        return {"error": "contact_data.email is required"}

    message = arguments.get("message")
    if not message:
        return {"error": "message is required"}

    name = contact_data.get("name") or "there"
    body = f"Hello {name},\n\n{message}"

    return {
        "recipients": [email],
        "subject": arguments.get("subject") or "Update",
        "body": body,
    }
