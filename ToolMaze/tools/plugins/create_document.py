"""
create_document Tool Plugin

Function: Save a text note to storage (simulated)
Category: Action
Domain: General
"""

TOOL_NAME = "create_document"


def execute(arguments, context) -> dict:
    """
    Save a text note (simulation)

    Args:
        arguments: Tool parameters
            - title (str): Note title
            - content (str): Note content
            - tags (list, optional): List of tags

    Returns:
        dict: Dictionary containing save status
    """
    # 提取必需参数 content
    content = arguments.get("content")
    if not content:
        return {
            "error": "Note content is required"
        }

    # 提取可选参数 title，缺省为 "Untitled"
    title = arguments.get("title") or "Untitled"

    # 提取可选参数 tags，缺省为空列表
    tags = arguments.get("tags") or []

    # 生成固定模拟 note_id
    note_id = "NOTE18E3D"

    # 返回保存结果与元数据
    return {
        "message": "Note saved successfully",
        "note_id": note_id,
        "title": title,
        "content_length": len(content),
        "tags": tags if tags else [],
    }
