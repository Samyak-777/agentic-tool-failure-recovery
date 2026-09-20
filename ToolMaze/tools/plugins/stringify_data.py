"""
stringify_data Tool Plugin

Function: Convert arbitrary structured data into plain text
Category: Processor
Domain: General
"""

import json

TOOL_NAME = "stringify_data"


def execute(arguments, context) -> dict:
    del context

    if "data" not in arguments:
        return {"error": "data is required"}

    data = arguments.get("data")
    if data is None:
        return {"error": "data must not be null"}

    if isinstance(data, str):
        serialized_text = data
        source_type = "str"
    else:
        source_type = type(data).__name__
        try:
            serialized_text = json.dumps(data, ensure_ascii=False, sort_keys=True)
        except TypeError:
            serialized_text = str(data)

    return {
        "serialized_text": serialized_text,
        "source_type": source_type,
        "preview": serialized_text[:120],
    }
