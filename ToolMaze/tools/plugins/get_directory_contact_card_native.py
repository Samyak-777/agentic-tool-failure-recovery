"""
get_directory_contact_card_native Tool Plugin

Function: Retrieve a directory-native contact card for a colleague
Category: Source
Domain: Office
"""

TOOL_NAME = "get_directory_contact_card_native"

from tools.plugins import get_contact_info as gci

CONSTRAINTS = gci.CONSTRAINTS


def execute(arguments, context) -> dict:
    name = arguments.get("name")
    if not name:
        return {"error": "name is required"}

    contact = gci._build_contact_result(name)
    if "error" in contact or not contact.get("found"):
        return contact

    user_id = contact.get("user_id") or "u_unknown"
    return {
        "card_id": f"dir_{user_id}",
        "display_name": contact.get("name") or str(name).title(),
        "primary_email": contact.get("email"),
        "org_unit": contact.get("department") or "unknown",
        "directory_user_id": user_id,
    }
