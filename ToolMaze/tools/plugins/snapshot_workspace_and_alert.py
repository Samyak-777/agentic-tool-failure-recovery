"""
snapshot_workspace_and_alert Tool Plugin

Function: Create a workspace snapshot and send a notification
Category: Action
Domain: General
"""

TOOL_NAME = "snapshot_workspace_and_alert"

CONSTRAINTS = {
    "priority": ["low", "medium", "high"],
    "channel": ["app", "sms", "email"],
}

from tools.plugins import snapshot_workspace as sw
from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    """Create a snapshot and notify the target user."""
    workspace_path = arguments.get("workspace_path")
    if not workspace_path:
        return {"error": "workspace_path is required"}

    backup_name = arguments.get("backup_name") or ""
    user_id = arguments.get("user_id") or "default_user"
    priority = arguments.get("priority") or "medium"
    channel = arguments.get("channel") or "app"

    snapshot_result = sw.execute(
        {
            "workspace_path": workspace_path,
            "backup_name": backup_name,
        },
        context,
    )
    if "error" in snapshot_result:
        return snapshot_result

    alert_result = pa.execute(
        {
            "message": snapshot_result.get("backup_id"),
            "user_id": user_id,
            "priority": priority,
            "channel": channel,
        },
        context,
    )
    if "error" in alert_result:
        return alert_result

    alert_result["backup_id"] = snapshot_result.get("backup_id")
    alert_result["workspace_path"] = snapshot_result.get("workspace_path")
    alert_result["backup_name"] = snapshot_result.get("backup_name")
    alert_result["size_mb"] = snapshot_result.get("size_mb")
    alert_result["backup_status"] = snapshot_result.get("status")
    alert_result["backup_timestamp"] = snapshot_result.get("timestamp")
    return alert_result
