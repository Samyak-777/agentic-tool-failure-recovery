"""
build_gnews_digest_report_payload Tool Plugin

Function: Fetch a GNews digest and build a text-first report payload
Category: Processor
Domain: General
"""

TOOL_NAME = "build_gnews_digest_report_payload"

from tools.plugins import build_news_text_report as bntr
from tools.plugins import get_news_gnews as gng


def execute(arguments, context) -> dict:
    news_data = gng.execute({"category": arguments.get("category")}, context)
    if "error" in news_data:
        return news_data

    report_payload = bntr.execute(
        {
            "news_data": news_data,
            "title": arguments.get("title") or "News Digest",
            "user_id": arguments.get("user_id") or "default_user",
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in report_payload:
        return report_payload

    report_payload["digest_category"] = news_data.get("category")
    report_payload["headline_count"] = news_data.get("count")
    return report_payload
