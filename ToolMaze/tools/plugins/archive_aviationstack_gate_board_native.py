"""
archive_aviationstack_gate_board_native Tool Plugin

Function: Archive an AviationStack-native gate board
Category: Action
Domain: Travel
"""

TOOL_NAME = "archive_aviationstack_gate_board_native"

from tools.plugins import create_document_and_alert_from_data as cdaafd


def execute(arguments, context) -> dict:
    gate_board = arguments.get("gate_board") or {}
    if not isinstance(gate_board, dict):
        return {"error": "gate_board must be an object"}

    result = cdaafd.execute(
        {
            "data": gate_board,
            "title": arguments.get("title") or "Gate Board",
            "tags": ["flight", "gate_board", "native"],
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
        "strategy": "aviationstack_gate_archive_native",
        "notification_id": result.get("notification_id"),
        "note_id": result.get("note_id"),
        "title": result.get("title"),
        "transport_ref": gate_board.get("board_ref") or "gate_board",
    }
