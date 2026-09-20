"""
publish_trip_timeline_notice_native Tool Plugin

Function: Publish a flight notice using a flightaware-native trip timeline
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_trip_timeline_notice_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    trip_timeline = arguments.get("trip_timeline") or {}
    if not isinstance(trip_timeline, dict):
        return {"error": "trip_timeline must be an object"}

    flight_no = trip_timeline.get("flight_no") or "UNKNOWN"
    latest_state = trip_timeline.get("latest_state") or "Status unavailable"
    route_text = trip_timeline.get("route_text") or "Unknown route"
    message = f"{flight_no} {latest_state} on {route_text}"
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
        "strategy": "trip_timeline_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "transport_ref": trip_timeline.get("timeline_id") or "trip_placeholder",
        "content": result.get("content", message),
    }
