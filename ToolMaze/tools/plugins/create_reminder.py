"""
create_reminder Tool Plugin

Function: Create a reminder/task (simulated)
Category: Action
Domain: Office
"""

TOOL_NAME = "create_reminder"

CONSTRAINTS = {
    "priority": ["low", "medium", "high"]
}

def execute(arguments, context) -> dict:
    """
    Create a reminder (simulation)

    Args:
        arguments: Tool parameters
            - title (str): Reminder title
            - datetime (str): Reminder time (YYYY-MM-DD HH:MM)
            - description (str, optional): Reminder description
            - priority (str, optional): Priority level (low, medium, high)

    Returns:
        dict: Dictionary containing reminder creation status
    """
    title = arguments.get("title")

    datetime_str = arguments.get("datetime")

    description = arguments.get("description") or ""

    priority = arguments.get("priority") or "medium"
    priority = priority.lower()

    # 验证必填参数
    if not datetime_str:
        return {
            "error": "Reminder datetime is required"
        }

    if not title:
        return {
            "error": "Reminder title is required"
        }

    # Validate priority
    if priority not in ["low", "medium", "high"]:
        priority = "medium"

    reminder_id = "REM7A3B2"

    return {
        "message": "Reminder created successfully",
        "reminder_id": reminder_id,
        "title": title,
        "datetime": datetime_str,
        "description": description,
        "priority": priority,
        "status": "active"
    }
