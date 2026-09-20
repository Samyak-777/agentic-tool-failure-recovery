"""
publish_directory_contact_card_native Tool Plugin

Function: Publish a directory-native contact card summary
Category: Action
Domain: Office
"""

TOOL_NAME = "publish_directory_contact_card_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    contact_card = arguments.get("contact_card") or {}
    if not isinstance(contact_card, dict):
        return {"error": "contact_card must be an object"}

    display_name = contact_card.get("display_name") or "Colleague"
    email = contact_card.get("primary_email") or "admin@company.com"
    message = f"Directory contact {display_name}: {email}"
    user_id = arguments.get("user_id") or "default_user"

    result = pa.execute(
        {
            "message": message,
            "user_id": user_id,
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "published",
        "strategy": "directory_contact_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "contact_ref": contact_card.get("card_id") or "dir_contact_card",
        "content": result.get("content", message),
    }
