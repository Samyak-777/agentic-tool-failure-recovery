"""
get_utc_moment_card_native Tool Plugin

Function: Retrieve a UTC-style native time moment card
Category: Source
Domain: General
"""

TOOL_NAME = "get_utc_moment_card_native"

from tools.plugins import get_current_time as gct


def execute(arguments, context) -> dict:
    time_data = gct.execute(arguments, context)
    if "error" in time_data:
        return time_data

    timestamp = time_data.get("timestamp", 0)
    return {
        "moment_card_id": f"moment_{timestamp}",
        "iso_stamp": time_data.get("iso_format"),
        "tz_label": time_data.get("timezone"),
        "day_name": time_data.get("weekday"),
        "clock_face": time_data.get("time"),
    }
