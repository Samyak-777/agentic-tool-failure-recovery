"""
send_directory_card_email_native Tool Plugin

Function: Send an email using a directory-native contact card
Category: Action
Domain: Office
"""

TOOL_NAME = "send_directory_card_email_native"

from tools.plugins import send_email as se


def execute(arguments, context) -> dict:
    contact_card = arguments.get("contact_card") or {}
    if not isinstance(contact_card, dict):
        return {"error": "contact_card must be an object"}

    email = contact_card.get("primary_email") or "admin@company.com"
    display_name = contact_card.get("display_name") or "Colleague"
    subject = arguments.get("subject") or "Update"
    message = arguments.get("message") or "Hello"

    result = se.execute(
        {
            "recipients": [email],
            "subject": subject,
            "body": f"Hello {display_name},\n\n{message}",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": result.get("status", "sent"),
        "strategy": "directory_email_native",
        "channel": "email",
        "target": email,
        "reference_id": contact_card.get("card_id") or "dir_placeholder",
        "user_id": contact_card.get("directory_user_id") or "u_placeholder",
    }
