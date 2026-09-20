"""
send_instant_message Tool Plugin

Function: Send a quick IM to a user (Substitute for send_email)
Category: Action
Domain: Office
"""
CONTACTS = {
    "alice": {"email": "alice@company.com", "phone": "+1-555-0101", "department": "Engineering", "user_id": "u_alice"},
    "bob": {"email": "bob@company.com", "phone": "+1-555-0102", "department": "Product", "user_id": "u_bob"},
    "charlie": {"email": "charlie@company.com", "phone": "+1-555-0103", "department": "Design", "user_id": "u_charlie"},
    "david": {"email": "david@company.com", "phone": "+1-555-0104", "department": "Marketing", "user_id": "u_david"},
}
import time

TOOL_NAME = "send_instant_message"

CONSTRAINTS = {
    "user_id": ["alice", "bob", "charlie", "david", "u_alice", "u_bob", "u_charlie", "u_david"]
}

def execute(arguments, context) -> dict:
    # Get message (required parameter)
    message = arguments.get("message")
    if not message:
        return {"error": "message content is required"}

    # Get user_id (optional parameter with reasonable default)
    user_id = arguments.get("user_id") or "alice"
    lookup_id = user_id[2:] if isinstance(user_id, str) and user_id.startswith("u_") else user_id

    if lookup_id not in CONTACTS:
        return {"error": f"User with ID '{user_id}' does not exist."}

    return {
        "status": "sent",
        "channel": "IM (Teams/Slack)",
        "recipient_id": user_id,
        "message_preview": message[:50] + "..." if len(message) > 50 else message
    }