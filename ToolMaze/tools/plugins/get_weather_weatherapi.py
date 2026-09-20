TOOL_NAME = "get_weather_weatherapi"

from tools.plugins import get_weather_openweather as gw

# 可替换工具组
ALTERNATIVE_TOOLS = gw.ALTERNATIVE_TOOLS

# Derive known cities from the weather plugin
KNOWN_CITIES = list(gw.CASES.keys())

CONSTRAINTS = {
    "city": list(gw.CASES.keys())
}


def execute(arguments, context):
    """获取天气信息"""
    city = arguments.get("city")

    # 检查是否已查询过该城市
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"city": city}
        )
        if existing:
            return existing

    return dict(gw.CASES.get(city, gw.DEFAULT))

