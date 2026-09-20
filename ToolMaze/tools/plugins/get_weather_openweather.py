TOOL_NAME = "get_weather_openweather"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_weather_openweather",
    "get_weather_weatherapi",
    "get_weather_visualcrossing",
    "get_weather_accuweather"
]

# Deterministic mapping of city -> weather
CASES = {
    "Tokyo": {"temperature_celsius": 22, "condition": "Sunny"},
    "Paris": {"temperature_celsius": 18, "condition": "Cloudy"},
    "New York": {"temperature_celsius": 15, "condition": "Rain"},
    "Beijing": {"temperature_celsius": 25, "condition": "Sunny"},
    "London": {"temperature_celsius": 12, "condition": "Rain"},
    "Sydney": {"temperature_celsius": 20, "condition": "Clear"},
    "Shanghai": {"temperature_celsius": 23, "condition": "Cloudy"},
}
DEFAULT = {"temperature_celsius": 20, "condition": "Clear"}

CONSTRAINTS = {
    "city": list(CASES.keys())
}


def execute(arguments, context):
    """
    获取天气信息

    Args:
        arguments: 工具参数
        context: ExecutionContext，可访问前序工具输出
    """
    city = arguments.get("city")

    # 检查是否已查询过该城市（任何替代工具）
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"city": city}
        )
        if existing:
            return existing

    return dict(CASES.get(city, DEFAULT))

