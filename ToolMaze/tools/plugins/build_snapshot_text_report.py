"""
build_snapshot_text_report Tool Plugin

Function: Build a text-based snapshot report payload
Category: Processor
Domain: General
"""

TOOL_NAME = "build_snapshot_text_report"


def execute(arguments, context) -> dict:
    del context

    snapshot_data = arguments.get("snapshot_data")
    if not isinstance(snapshot_data, dict):
        return {"error": "snapshot_data must be an object"}

    title = arguments.get("title") or "Workspace Snapshot"
    content = "\n".join([
        f"Workspace: {snapshot_data.get('workspace_path')}",
        f"Backup ID: {snapshot_data.get('backup_id')}",
        f"Backup Name: {snapshot_data.get('backup_name')}",
        f"Size (MB): {snapshot_data.get('size_mb')}",
        f"Status: {snapshot_data.get('backup_status') or snapshot_data.get('status')}",
        f"Timestamp: {snapshot_data.get('backup_timestamp') or snapshot_data.get('timestamp')}",
    ])

    return {
        "title": title,
        "content": content,
        "tags": ["snapshot", snapshot_data.get("status") or "unknown"],
        "user_id": arguments.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
