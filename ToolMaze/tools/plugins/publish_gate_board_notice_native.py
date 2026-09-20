"""
publish_gate_board_notice_native Tool Plugin

Function: Publish a flight notice using an aviation-native gate board
Category: Action
Domain: Travel
"""

TOOL_NAME = "publish_gate_board_notice_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    gate_board = arguments.get("gate_board") or {}
    if not isinstance(gate_board, dict):
        return {"error": "gate_board must be an object"}

    flight_code = gate_board.get("flight_code") or "UNKNOWN"
    gate_label = gate_board.get("gate_label") or "TBD"
    status_text = gate_board.get("status_text") or "Status unavailable"
    message = f"{flight_code} {status_text} at gate {gate_label}"
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
        "strategy": "gate_board_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "transport_ref": gate_board.get("board_ref") or "gate_placeholder",
        "content": result.get("content", message),
    }
