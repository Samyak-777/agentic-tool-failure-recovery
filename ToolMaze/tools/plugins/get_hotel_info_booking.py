TOOL_NAME = "get_hotel_info_booking"

from tools.plugins import get_hotel_info as gh

ALTERNATIVE_TOOLS = gh.ALTERNATIVE_TOOLS
CASES = gh.CASES
DEFAULT = gh.DEFAULT

CONSTRAINTS = {
    "hotel_name": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """获取酒店信息（Booking）"""
    hotel_name = arguments.get("hotel_name")

    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"hotel_name": hotel_name}
        )
        if existing:
            return existing

    return dict(CASES.get(hotel_name, DEFAULT))
