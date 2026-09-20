"""
get_gnews_digest_cards_native Tool Plugin

Function: Retrieve a GNews-native digest card bundle
Category: Source
Domain: General
"""

TOOL_NAME = "get_gnews_digest_cards_native"

from tools.plugins import get_news_gnews as gng

CONSTRAINTS = gng.CONSTRAINTS


def execute(arguments, context) -> dict:
    category = (arguments.get("category") or "").lower()
    if not category:
        return {"error": "category is required"}

    news = gng.execute({"category": category}, context)
    if "error" in news:
        return news

    headlines = news.get("headlines") or []
    cards = [
        {"headline": headline, "rank": idx + 1}
        for idx, headline in enumerate(headlines)
    ]
    return {
        "digest_id": f"gdc_{category}",
        "topic": news.get("category", category),
        "cards": cards,
        "source": "gnews",
    }
