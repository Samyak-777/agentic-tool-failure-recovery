TOOL_NAME = "get_meeting_rooms_workplace"

from tools.plugins import get_meeting_rooms as gmr

ALTERNATIVE_TOOLS = gmr.ALTERNATIVE_TOOLS



def execute(arguments, context) -> dict:
    """Retrieve meeting rooms using a Workplace-style provider."""
    raw_min_capacity = arguments.get("min_capacity")
    raw_date = arguments.get("date")
    raw_start_time = arguments.get("start_time")

    if hasattr(context, "find_alternative_output"):
        args_match = {}
        if raw_min_capacity is not None:
            args_match["min_capacity"] = raw_min_capacity
        if raw_date is not None:
            args_match["date"] = raw_date
        if raw_start_time is not None:
            args_match["start_time"] = raw_start_time
        if args_match:
            existing = context.find_alternative_output(ALTERNATIVE_TOOLS, args_match)
            if existing:
                return existing

    min_capacity = raw_min_capacity or 0
    return gmr._build_rooms_result(min_capacity, raw_date, raw_start_time, context)
