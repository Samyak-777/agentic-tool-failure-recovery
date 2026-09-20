"""
publish_currents_bulletin_pack_native Tool Plugin

Function: Publish a news notice using a Currents-native bulletin pack
Category: Action
Domain: General
"""

TOOL_NAME = "publish_currents_bulletin_pack_native"

from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    bulletin_pack = arguments.get("bulletin_pack") or {}
    if not isinstance(bulletin_pack, dict):
        return {"error": "bulletin_pack must be an object"}

    bulletins = bulletin_pack.get("bulletins") or []
    title = bulletins[0].get("title") if bulletins and isinstance(bulletins[0], dict) else "News update"
    message = f"{bulletin_pack.get('vertical', 'general')}: {title}"
    user_id = arguments.get("user_id") or "default_user"
    result = pa.execute(
        {
            "message": message,
            "user_id": user_id,
            "priority": arguments.get("priority") or "medium",
            "channel": arguments.get("channel") or "app",
        },
        context,
    )
    if "error" in result:
        return result

    return {
        "status": "published",
        "strategy": "currents_notice_native",
        "notification_id": result.get("notification_id"),
        "target_user": user_id,
        "news_ref": bulletin_pack.get("pack_id") or "currents_bulletin_pack",
        "content": result.get("content", message),
    }
