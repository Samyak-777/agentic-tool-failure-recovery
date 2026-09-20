TOOL_NAME = "query_availability_google_calendar"

from tools.plugins import query_availability as qa

ALTERNATIVE_TOOLS = qa.ALTERNATIVE_TOOLS
CONSTRAINTS = qa.CONSTRAINTS



def execute(arguments, context) -> dict:
    """Query availability using a Google Calendar-style provider."""
    item_id = arguments.get("item_id")
    if not item_id:
        return {"error": "item_id is required"}

    raw_start_date = arguments.get("start_date")
    if hasattr(context, "find_alternative_output"):
        args_match = {"item_id": item_id}
        if raw_start_date is not None:
            args_match["start_date"] = raw_start_date
        existing = context.find_alternative_output(ALTERNATIVE_TOOLS, args_match)
        if existing:
            return existing

    start_date = raw_start_date or "2024-10-24"
    return qa._build_availability_result(item_id, start_date, context)
