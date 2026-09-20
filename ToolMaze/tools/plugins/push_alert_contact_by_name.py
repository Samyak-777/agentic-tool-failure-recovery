"""
push_alert_contact_by_name Tool Plugin

Function: Resolve a contact by name and send a push alert
Category: Action
Domain: Office
"""

TOOL_NAME = "push_alert_contact_by_name"

from tools.plugins import get_contact_info as gci
from tools.plugins import push_alert as pa

CONSTRAINTS = {
    "name": gci.CONSTRAINTS["name"],
    "priority": ["low", "medium", "high"],
    "channel": ["app", "sms", "email"],
}



def execute(arguments, context) -> dict:
    """Look up a contact by name and send them a push alert."""
    name = arguments.get("name")
    message = arguments.get("message")
    priority = arguments.get("priority") or "medium"
    channel = arguments.get("channel") or "app"

    if not name:
        return {"error": "name is required"}
    if not message:
        return {"error": "message is required"}

    contact_result = gci.execute({"name": name}, context)
    if "error" in contact_result or not contact_result.get("found"):
        return contact_result

    alert_result = pa.execute(
        {
            "message": message,
            "user_id": contact_result.get("user_id"),
            "priority": priority,
            "channel": channel,
        },
        context,
    )
    if "error" in alert_result:
        return alert_result

    alert_result["resolved_name"] = contact_result.get("name")
    alert_result["recipient_email"] = contact_result.get("email")
    return alert_result
