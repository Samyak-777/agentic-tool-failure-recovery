"""
snapshot_workspace_report_and_alert Tool Plugin

Function: Snapshot a workspace, build a text report, and notify the user
Category: Action
Domain: General
"""

TOOL_NAME = "snapshot_workspace_report_and_alert"

from tools.plugins import build_snapshot_text_report as bstr
from tools.plugins import create_document_and_alert as cdaa
from tools.plugins import snapshot_workspace as sw


def execute(arguments, context) -> dict:
    snapshot_data = sw.execute(
        {
            "workspace_path": arguments.get("workspace_path"),
            "backup_name": arguments.get("backup_name") or "",
        },
        context,
    )
    if "error" in snapshot_data:
        return snapshot_data

    report_payload = bstr.execute(
        {
            "snapshot_data": snapshot_data,
            "title": arguments.get("title") or "Workspace Snapshot",
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in report_payload:
        return report_payload

    result = cdaa.execute(
        {
            "content": report_payload.get("content"),
            "title": report_payload.get("title"),
            "tags": report_payload.get("tags"),
            "user_id": report_payload.get("user_id"),
            "priority": report_payload.get("priority"),
            "channel": report_payload.get("channel"),
        },
        context,
    )
    if "error" in result:
        return result

    result["backup_id"] = snapshot_data.get("backup_id")
    result["backup_name"] = snapshot_data.get("backup_name")
    result["workflow"] = "snapshot_report_document"
    return result
