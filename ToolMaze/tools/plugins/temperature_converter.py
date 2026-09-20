TOOL_NAME = "temperature_converter"

CONSTRAINTS = {
    "from_unit": ["celsius", "fahrenheit"],
    "to_unit": ["celsius", "fahrenheit"]
}

def execute(arguments, context):
    """温度单位转换"""
    # Get value (from arguments)
    value = arguments.get("value")

    try:
        value = float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return {"error": "Invalid temperature value"}

    # Get from_unit (optional parameter with reasonable default)
    from_unit = arguments.get("from_unit") or "celsius"
    from_unit = from_unit.lower()

    # Get to_unit (optional parameter with reasonable default)
    to_unit = arguments.get("to_unit") or "fahrenheit"
    to_unit = to_unit.lower()

    # 转换逻辑
    if from_unit == to_unit:
        converted = value
    elif from_unit == "celsius" and to_unit == "fahrenheit":
        converted = value * 9/5 + 32
    elif from_unit == "fahrenheit" and to_unit == "celsius":
        converted = (value - 32) * 5/9
    elif from_unit == "celsius" and to_unit == "kelvin":
        converted = value + 273.15
    elif from_unit == "kelvin" and to_unit == "celsius":
        converted = value - 273.15
    elif from_unit == "fahrenheit" and to_unit == "kelvin":
        converted = (value - 32) * 5/9 + 273.15
    elif from_unit == "kelvin" and to_unit == "fahrenheit":
        converted = (value - 273.15) * 9/5 + 32
    else:
        return {"error": f"Unsupported conversion: {from_unit} to {to_unit}"}

    return {
        "converted_value": round(converted, 2),
        "from_unit": from_unit,
        "to_unit": to_unit,
        "original_value": value
    }

