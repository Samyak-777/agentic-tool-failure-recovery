"""
create_gnews_digest_and_alert Tool Plugin

Function: Fetch a GNews digest, build a text report, and notify the user
Category: Action
Domain: General
"""

TOOL_NAME = "create_gnews_digest_and_alert"

from tools.plugins import build_news_text_report as bntr
from tools.plugins import create_document_and_alert as cdaa
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

    result = cdaa.execute(
        {
            "content": report_payload.get("content"),
            "title": report_payload.get("title"),
            "tags": report_payload.get("tags"),
            "user_id": report_payload.get("user_id"),
            "priority": report_payload.get("priority"),
            "channel": report_payload.get("channel"),
        },
        context,
    )
    if "error" in result:
        return result

    result["digest_category"] = news_data.get("category")
    result["headline_count"] = news_data.get("count")
    result["workflow"] = "gnews_digest_document"
    return result
