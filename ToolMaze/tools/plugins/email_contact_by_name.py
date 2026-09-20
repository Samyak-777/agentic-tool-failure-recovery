"""
email_contact_by_name Tool Plugin

Function: Resolve a contact by name and send email
Category: Action
Domain: Office
"""

TOOL_NAME = "email_contact_by_name"

from tools.plugins import get_contact_info as gci
from tools.plugins import send_email as se

CONSTRAINTS = gci.CONSTRAINTS



def execute(arguments, context) -> dict:
    """Look up a contact by name and send them an email."""
    name = arguments.get("name")
    body = arguments.get("body")
    subject = arguments.get("subject") or "No Subject"

    if not name:
        return {"error": "name is required"}
    if not body:
        return {"error": "body is required"}

    contact_result = gci.execute({"name": name}, context)
    if "error" in contact_result or not contact_result.get("found"):
        return contact_result

    email_result = se.execute(
        {
            "body": body,
            "recipients": [contact_result.get("email")],
            "subject": subject,
        },
        context,
    )
    if "error" in email_result:
        return email_result

    email_result["resolved_name"] = contact_result.get("name")
    email_result["user_id"] = contact_result.get("user_id")
    return email_result
