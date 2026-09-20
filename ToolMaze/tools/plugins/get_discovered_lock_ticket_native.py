"""
get_discovered_lock_ticket_native Tool Plugin

Function: Retrieve a native lock ticket from discovered smart devices
Category: Source
Domain: IoT
"""

TOOL_NAME = "get_discovered_lock_ticket_native"

from tools.plugins import discover_smart_devices as dsd
from tools.plugins import select_discovered_device_by_type as sddbt


def execute(arguments, context) -> dict:
    area = arguments.get("area")
    discovery = dsd.execute({"location": area}, context)
    if "error" in discovery:
        return discovery

    device_ref = sddbt.execute(
        {
            "discovery_data": discovery,
            "device_type": "smart_lock",
        },
        context,
    )
    if "error" in device_ref:
        return device_ref

    return {
        "lock_ticket_id": f"disc_{device_ref.get('device_id', 'lock')}",
        "lock_device_id": device_ref.get("device_id"),
        "source_area": device_ref.get("location") or area,
        "selection_mode": device_ref.get("selection_reason") or "discovered",
        "source_label": "discovery_scan",
    }
