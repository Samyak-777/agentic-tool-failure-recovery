"""
publish_booking_stay_sheet_native Tool Plugin

Function: Publish a hotel notice using a Booking-native stay sheet
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_booking_stay_sheet_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    stay_sheet = arguments.get("stay_sheet") or {}
    if not isinstance(stay_sheet, dict):
        return {"error": "stay_sheet must be an object"}

    message = (
        f"{stay_sheet.get('property_name', 'Hotel')} "
        f"{stay_sheet.get('availability_state', 'Unknown')} at "
        f"{stay_sheet.get('nightly_usd', 0)} USD/night"
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
        "strategy": "booking_stay_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "property_ref": stay_sheet.get("stay_sheet_id") or "booking_stay_sheet",
        "content": result.get("content", message),
    }
