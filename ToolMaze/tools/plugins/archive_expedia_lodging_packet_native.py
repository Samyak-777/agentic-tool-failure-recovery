"""
archive_expedia_lodging_packet_native Tool Plugin

Function: Archive an Expedia-native lodging packet
Category: Action
Domain: Travel
"""

TOOL_NAME = "archive_expedia_lodging_packet_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    lodging_packet = arguments.get("lodging_packet") or {}
    if not isinstance(lodging_packet, dict):
        return {"error": "lodging_packet must be an object"}

    result = cdaafd.execute(
        {
            "data": lodging_packet,
            "title": arguments.get("title") or "Lodging Packet",
            "tags": ["hotel", "expedia", "native"],
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "archived",
        "strategy": "expedia_lodging_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "property_ref": lodging_packet.get("lodging_packet_id") or "expedia_lodging",
    }
