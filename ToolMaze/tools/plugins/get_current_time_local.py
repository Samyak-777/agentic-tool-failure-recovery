"""
get_current_time_local Tool Plugin

Function: Get current system time using a local-time style provider
Category: Source
Domain: General
"""

TOOL_NAME = "get_current_time_local"

from tools.plugins import get_current_time as gct

CONSTRAINTS = gct.CONSTRAINTS


def execute(arguments, context) -> dict:
    return gct.execute(arguments, context)
