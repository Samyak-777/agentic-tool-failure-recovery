"""
get_currents_bulletin_pack_native Tool Plugin

Function: Retrieve a Currents-native bulletin pack
Category: Source
Domain: General
"""

TOOL_NAME = "get_currents_bulletin_pack_native"

from tools.plugins import get_news_currents as gnc

CONSTRAINTS = gnc.CONSTRAINTS


def execute(arguments, context) -> dict:
    category = (arguments.get("category") or "").lower()
    if not category:
        return {"error": "category is required"}

    news = gnc.execute({"category": category}, context)
    if "error" in news:
        return news

    headlines = news.get("headlines") or []
    bulletins = [
        {"title": headline, "order": idx + 1}
        for idx, headline in enumerate(headlines)
    ]
    return {
        "pack_id": f"cbp_{category}",
        "vertical": news.get("category", category),
        "bulletins": bulletins,
        "source": "currents",
    }
