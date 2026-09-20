"""
resolve_directory_contact_identity Tool Plugin

Function: Resolve a normalized contact identity profile from directory contact data
Category: Processor
Domain: Office
"""

TOOL_NAME = "resolve_directory_contact_identity"


def execute(arguments, context) -> dict:
    del context

    contact_data = arguments.get("contact_data")
    if not isinstance(contact_data, dict):
        return {"error": "contact_data must be an object"}
    if contact_data.get("found") is False:
        return {"error": contact_data.get("error") or "contact_data did not resolve a contact"}

    user_id = contact_data.get("user_id")
    if not user_id:
        return {"error": "contact_data.user_id is required"}

    display_name = contact_data.get("name") or (arguments.get("name") or "").strip().title() or "Unknown"
    department = contact_data.get("department") or "unknown"
    contact_value = contact_data.get("email")
    if not contact_value:
        return {"error": "contact_data.email is required"}

    return {
        "identity_method": "directory_contact",
        "display_name": display_name,
        "user_id": user_id,
        "department": department,
        "contact_channel": "email",
        "contact_value": contact_value,
    }
