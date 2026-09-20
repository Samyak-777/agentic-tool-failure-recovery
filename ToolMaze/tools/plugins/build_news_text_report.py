"""
build_news_text_report Tool Plugin

Function: Build a text-first news digest payload
Category: Processor
Domain: General
"""

TOOL_NAME = "build_news_text_report"


def execute(arguments, context) -> dict:
    del context

    news_data = arguments.get("news_data")
    if not isinstance(news_data, dict):
        return {"error": "news_data must be an object"}

    category = news_data.get("category") or "general"
    headlines = news_data.get("headlines") or []
    title = arguments.get("title") or "News Digest"
    user_id = arguments.get("user_id") or "default_user"
    priority = arguments.get("priority") or "medium"
    channel = arguments.get("channel") or "app"

    lines = [f"Category: {category}", "Headlines:"]
    for idx, headline in enumerate(headlines, 1):
        lines.append(f"{idx}. {headline}")

    return {
        "title": title,
        "content": "\n".join(lines),
        "tags": ["news", category],
        "user_id": user_id,
        "priority": priority,
        "channel": channel,
    }
