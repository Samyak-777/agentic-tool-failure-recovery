"""
create_document_and_alert_from_data Tool Plugin

Function: Serialize arbitrary data, create a document, and send a notification
Category: Action
Domain: General
"""

import json

TOOL_NAME = "create_document_and_alert_from_data"

from tools.plugins import create_document_and_alert as cdaa

CONSTRAINTS = {
    "priority": ["low", "medium", "high"],
    "channel": ["app", "sms", "email"],
}


def _stringify(data):
    if isinstance(data, str):
        return data, "str"
    source_type = type(data).__name__
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True), source_type
    except TypeError:
        return str(data), source_type


def execute(arguments, context) -> dict:
    if "data" not in arguments:
        return {"error": "data is required"}
    if arguments.get("data") is None:
        return {"error": "data must not be null"}

    serialized_text, source_type = _stringify(arguments.get("data"))
    result = cdaa.execute(
        {
            "title": arguments.get("title") or "Untitled",
            "content": serialized_text,
            "tags": arguments.get("tags") or [],
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    result["source_type"] = source_type
    result["serialized_preview"] = serialized_text[:120]
    return result
