"""
get_field_value Tool Plugin

Function: Extract a specific value from a dictionary or a list of items.
Category: Processor
Domain: General
"""

import json

TOOL_NAME = "get_field_value"

def execute(arguments, context) -> dict:
    """
    Extracts data from a complex structure (List or Dict).
    
    Args:
        arguments:
            - data: The source object (List, Dict, or JSON string).
            - target_field: (Optional) The key to extract if data is a dict.
            - index: (Optional) The index to extract if data is a list (default 0).
    """
    # Get data (from arguments)
    raw_data = arguments.get("data")

    # Get target_field (optional parameter)
    target_field = arguments.get("target_field") or ""

    # field_name is an alias for target_field
    field_name = arguments.get("field_name")
    if field_name:
        target_field = field_name

    # Get index (optional parameter with reasonable default)
    index = arguments.get("index") or 0

    if raw_data is None:
        return {"error": "Data input is required"}

    # 1. Parsing: Handle case where LLM passes a JSON string instead of an object
    data = raw_data
    if isinstance(raw_data, str):
        try:
            # Try to parse string as JSON structure
            data = json.loads(raw_data)
        except json.JSONDecodeError:
            # If it's just a regular string, keep it as is
            pass

    extracted_value = None

    # 2. Extraction Logic
    try:
        # Scenario A: Data is a List
        if isinstance(data, list):
            try:
                idx = int(index)
            except (ValueError, TypeError):
                return {"error": f"Invalid index format: {index}"}

            if len(data) == 0:
                return {"error": "Data list is empty"}
            
            if idx < 0 or idx >= len(data):
                return {"error": f"Index {idx} out of range (length: {len(data)})"}

            item = data[idx]
            
            # If item is a dict and we need a specific field inside that item
            if isinstance(item, dict) and target_field:
                extracted_value = item.get(target_field)
                if extracted_value is None:
                    return {"error": f"Field '{target_field}' not found in item at index {idx}"}
            else:
                # Just return the item itself (e.g., list of strings)
                extracted_value = item

        # Scenario B: Data is a Dictionary
        elif isinstance(data, dict):
            if target_field:
                extracted_value = data.get(target_field)
                if extracted_value is None:
                    return {"error": f"Field '{target_field}' not found in data"}
            else:
                # Fallback: YAML description mentions "default: first key" behavior or return full dict
                # Here we default to returning the full dict if no key specified,
                # unless data implies we should just grab the first available value (common for single-key dicts)
                if len(data) > 0:
                    extracted_value = list(data.values())[0]
                else:
                    extracted_value = data # Return as is if no specific target

        # Scenario C: Data is a scalar value (int, float, str, bool) - passthrough
        elif isinstance(data, (int, float, str, bool)):
            extracted_value = data

        else:
            return {
                "error": f"Unsupported data type: {type(data).__name__}. Expected List or Dict."
            }

    except Exception as e:
        return {"error": f"Extraction failed: {str(e)}"}

    return {
        "source_type": type(data).__name__,
        "extracted_value": extracted_value
    }