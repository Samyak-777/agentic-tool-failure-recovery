"""
create_document_and_alert Tool Plugin

Function: Create a document and send a notification
Category: Action
Domain: General
"""

TOOL_NAME = "create_document_and_alert"

CONSTRAINTS = {
    "priority": ["low", "medium", "high"],
    "channel": ["app", "sms", "email"],
}

from tools.plugins import create_document as cd
from tools.plugins import push_alert as pa


def execute(arguments, context) -> dict:
    """Create a document and notify the target user."""
    # 提取必需参数 content
    content = arguments.get("content")
    if not content:
        return {"error": "content is required"}

    # 提取可选参数并设置缺省值
    title = arguments.get("title") or "Untitled"
    tags = arguments.get("tags") or []
    user_id = arguments.get("user_id") or "default_user"
    priority = arguments.get("priority") or "medium"
    channel = arguments.get("channel") or "app"

    # 先创建文档
    document_result = cd.execute(
        {
            "content": content,
            "title": title,
            "tags": tags,
        },
        context,
    )
    # 文档创建失败则直接返回错误
    if "error" in document_result:
        return document_result

    # 再发送通知，使用文档标题作为消息内容
    alert_result = pa.execute(
        {
            "message": document_result.get("title", title),
            "user_id": user_id,
            "priority": priority,
            "channel": channel,
        },
        context,
    )
    # 通知发送失败则直接返回错误
    if "error" in alert_result:
        return alert_result

    # 将文档信息合并到通知结果中返回
    alert_result["note_id"] = document_result.get("note_id")
    alert_result["title"] = document_result.get("title")
    alert_result["tags"] = document_result.get("tags", [])
    alert_result["content"] = content
    return alert_result
