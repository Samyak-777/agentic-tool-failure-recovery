"""
publish_expedia_lodging_packet_native Tool Plugin

Function: Publish a hotel notice using an Expedia-native lodging packet
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_expedia_lodging_packet_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    lodging_packet = arguments.get("lodging_packet") or {}
    if not isinstance(lodging_packet, dict):
        return {"error": "lodging_packet must be an object"}

    message = (
        f"{lodging_packet.get('hotel_label', 'Hotel')} "
        f"{lodging_packet.get('inventory_state', 'Unknown')} at "
        f"{lodging_packet.get('rate_amount', 0)} USD/night"
    )
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
        "strategy": "expedia_lodging_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "property_ref": lodging_packet.get("lodging_packet_id") or "expedia_lodging_packet",
        "content": result.get("content", message),
    }
