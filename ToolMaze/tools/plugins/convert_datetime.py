"""
convert_datetime Tool Plugin

Function: Convert Unix timestamp to human-readable datetime string
Category: Processor
Domain: General
"""

TOOL_NAME = "convert_datetime"

import time

def execute(arguments, context) -> dict:
    """转换时间戳"""
    timestamp = arguments.get("timestamp")
    
    # 1. Validate input type
    if not isinstance(timestamp, int):
        return {
            "error": f"Invalid timestamp type: {type(timestamp).__name__}. Expected integer."
        }
    
    # 2. Validate timestamp range (between year 1970 and 2100)
    try:
        # Convert to struct_time to validate
        time_struct = time.gmtime(timestamp)
        
        # Basic sanity check (year between 1970-2100)
        year = time_struct.tm_year
        if not (1970 <= year <= 2100):
            return {
                "error": f"Timestamp out of valid range (1970-2100). Year: {year}"
            }
    except (OverflowError, OSError, ValueError) as e:
        return {
            "error": f"Invalid timestamp value: {str(e)}"
        }
    
    # 3. Format to required string format (UTC time)
    formatted_time = time.strftime("%Y-%m-%d %H:%M", time_struct)
    
    return {
        "original_timestamp": timestamp,
        "formatted_time": formatted_time,
    }