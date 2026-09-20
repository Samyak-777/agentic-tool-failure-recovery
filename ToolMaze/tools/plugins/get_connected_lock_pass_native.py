"""
get_connected_lock_pass_native Tool Plugin

Function: Retrieve a native lock pass from connected-device inventory
Category: Source
Domain: IoT
"""

TOOL_NAME = "get_connected_lock_pass_native"

from tools.plugins import query_connected_devices as qcd
from tools.plugins import resolve_connected_device_by_type as rcdbt


def execute(arguments, context) -> dict:
    area = arguments.get("area")
    connected = qcd.execute({"area": area, "device_type": "smart_lock"}, context)
    if "error" in connected:
        return connected

    device_ref = rcdbt.execute(
        {
            "connected_data": connected,
            "device_type": "smart_lock",
        },
        context,
    )
    if "error" in device_ref:
        return device_ref

    return {
        "lock_pass_ref": f"conn_{device_ref.get('device_id', 'lock')}",
        "lock_device_id": device_ref.get("device_id"),
        "source_area": device_ref.get("area") or area,
        "selection_mode": device_ref.get("selection_reason") or "connected",
        "source_label": "connected_inventory",
    }
