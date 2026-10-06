"""semantic_validation test fixtures."""

MOCK_TOOL_DEFINITIONS = {
    "get_weather_openweather": {
        "paradigms": {
            "mcp": {
                "output_schema": {
                    "temperature_celsius": {"type": "integer"},
                    "condition": {"type": "string"},
                }
            }
        }
    },
    "get_stock_yahoo_finance": {
        "paradigms": {
            "mcp": {
                "output_schema": {
                    "price_usd": {"type": "number"},
                    "currency": {"type": "string"},
                }
            }
        }
    },
    "query_availability": {
        "paradigms": {
            "mcp": {
                "output_schema": {
                    "total_slots": {"type": "integer"},
                    "free_slots": {"type": "array", "items": {"type": "string"}},
                }
            }
        }
    },
    "no_schema_tool": {
        "paradigms": {}
    }
}


class MockToolLoader:
    def __init__(self, definitions=None):
        self.definitions = definitions or MOCK_TOOL_DEFINITIONS

    def get_tool_by_name(self, name: str):
        return self.definitions.get(name)
