"""
get_current_time Tool Plugin

Function: Get current system time and date
Category: Source
Domain: General
"""

from datetime import datetime, timezone, timedelta

TOOL_NAME = "get_current_time"

CONSTRAINTS = {
    "timezone": ["UTC", "GMT", "EST", "EDT", "CST", "CDT", "MST", "MDT", "PST", "PDT", "JST",
                 "Asia/Tokyo", "Asia/Shanghai", "Asia/Hong_Kong", "Europe/London", "Europe/Paris",
                 "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"]
}

# Simplified timezone mapping (offset from UTC in hours)
TIMEZONE_OFFSETS = {
    "UTC": 0,
    "GMT": 0,
    "EST": -5,
    "EDT": -4,
    "CST": -6,
    "CDT": -5,
    "MST": -7,
    "MDT": -6,
    "PST": -8,
    "PDT": -7,
    "JST": 9,
    "Asia/Tokyo": 9,
    "Asia/Shanghai": 8,
    "Asia/Hong_Kong": 8,
    "Europe/London": 0,
    "Europe/Paris": 1,
    "America/New_York": -5,
    "America/Chicago": -6,
    "America/Denver": -7,
    "America/Los_Angeles": -8,
}


def execute(arguments, context) -> dict:
    """
    Get current system time and date

    Args:
        arguments: Tool parameters
            - timezone (str, optional): Timezone, defaults to 'UTC'

    Returns:
        dict: Dictionary containing the following keys
            - datetime: Complete datetime string (YYYY-MM-DD HH:MM:SS)
            - date: Date string (YYYY-MM-DD)
            - time: Time string (HH:MM:SS)
            - timestamp: Unix timestamp
            - timezone: Timezone string
    """
    timezone_str = arguments.get("timezone") or "UTC"

    # Get offset for the timezone
    offset_hours = TIMEZONE_OFFSETS.get(timezone_str, 0)

    # Create timezone object
    tz = timezone(timedelta(hours=offset_hours))

    # Use fixed time for deterministic output
    fixed_utc = datetime(2026, 2, 22, 15, 4, 54, 104554, tzinfo=timezone.utc)
    now = fixed_utc.astimezone(tz)

    return {
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timestamp": int(now.timestamp()),
        "timezone": timezone_str,
        "weekday": now.strftime("%A"),
        "iso_format": now.isoformat()
    }
