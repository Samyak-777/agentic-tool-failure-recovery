"""
get_local_time_capsule_native Tool Plugin

Function: Retrieve a local-time native capsule
Category: Source
Domain: General
"""

TOOL_NAME = "get_local_time_capsule_native"

from tools.plugins import get_current_time_local as gctl


def execute(arguments, context) -> dict:
    time_data = gctl.execute(arguments, context)
    if "error" in time_data:
        return time_data

    timestamp = time_data.get("timestamp", 0)
    return {
        "capsule_ref": f"capsule_{timestamp}",
        "local_clock": time_data.get("time"),
        "calendar_day": time_data.get("date"),
        "timezone_key": time_data.get("timezone"),
        "weekday_title": time_data.get("weekday"),
    }
