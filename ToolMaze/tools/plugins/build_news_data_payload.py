"""
build_news_data_payload Tool Plugin

Function: Build a structured news digest payload
Category: Processor
Domain: General
"""

TOOL_NAME = "build_news_data_payload"


def execute(arguments, context) -> dict:
    del context

    news_data = arguments.get("news_data")
    if not isinstance(news_data, dict):
        return {"error": "news_data must be an object"}

    category = news_data.get("category") or "general"
    title = arguments.get("title") or "News Digest"

    return {
        "data": {
            "category": category,
            "headlines": news_data.get("headlines") or [],
            "count": news_data.get("count") or len(news_data.get("headlines") or []),
        },
        "title": title,
        "tags": ["news", category, "structured"],
        "user_id": arguments.get("user_id") or "default_user",
        "priority": arguments.get("priority") or "medium",
        "channel": arguments.get("channel") or "app",
    }
