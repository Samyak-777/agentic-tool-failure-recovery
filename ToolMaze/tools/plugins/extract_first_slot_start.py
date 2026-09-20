"""
extract_first_slot_start Tool Plugin
Category: Processor
Domain: Office
"""

TOOL_NAME = "extract_first_slot_start"


def execute(arguments, context) -> dict:
    slots = arguments.get("slots") or []
    if not isinstance(slots, list) or not slots:
        return {"error": "slots must be a non-empty list"}

    first = slots[0]
    if not isinstance(first, dict):
        return {"error": "slot entry must be an object"}

    start_time = first.get("start_time")
    if not start_time:
        return {"error": "first slot does not contain start_time"}

    return {
        "extracted_value": start_time,
        "slot_index": 0,
    }
