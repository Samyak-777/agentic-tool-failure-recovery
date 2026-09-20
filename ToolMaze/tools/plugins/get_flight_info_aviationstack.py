TOOL_NAME = "get_flight_info_aviationstack"

from tools.plugins import get_flight_info as gf

ALTERNATIVE_TOOLS = gf.ALTERNATIVE_TOOLS
CASES = gf.CASES
DEFAULT = gf.DEFAULT

CONSTRAINTS = {
    "flight_number": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """获取航班信息（Aviationstack）"""
    flight_number = (arguments.get("flight_number") or "").upper()

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"flight_number": flight_number}
        )
        if existing:
            return existing

    return dict(CASES.get(flight_number, DEFAULT))
