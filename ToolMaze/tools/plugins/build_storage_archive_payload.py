"""
build_storage_archive_payload Tool Plugin

Function: Build a structured storage-archive payload from a storage listing
Category: Processor
Domain: General
"""

TOOL_NAME = "build_storage_archive_payload"


def execute(arguments, context) -> dict:
    del context

    storage_data = arguments.get("storage_data")
    if not isinstance(storage_data, dict):
        return {"error": "storage_data must be an object"}

    folder = storage_data.get("folder") or "unknown_folder"

    return {
        "data": {
            "folder": folder,
            "matched_count": storage_data.get("matched_count", 0),
            "total_count": storage_data.get("total_count", 0),
            "files": storage_data.get("files") or [],
        },
        "title": arguments.get("title") or "Storage Archive",
        "tags": ["storage", folder.strip("/") or "root"],
        "user_id": arguments.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
