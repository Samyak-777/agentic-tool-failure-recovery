"""
order_items Tool Plugin

Function: Sort a list of items in ascending or descending order
Category: Processor
Domain: General
"""

TOOL_NAME = "order_items"

CONSTRAINTS = {
    "order": ["asc", "desc"]
}

def execute(arguments, context) -> dict:
    """
    Sort a list of items

    Args:
        arguments: Tool parameters
            - items (list): List of items to sort
            - order (str): Sort order, 'asc' or 'desc' (default: 'asc')
            - key (str, optional): If items are dicts, sort by this key

    Returns:
        dict: Dictionary containing sorted items
    """
    # Get items (from arguments)
    items = arguments.get("items") or []

    # Get order (optional parameter with reasonable default)
    order = arguments.get("order") or "asc"
    order = order.lower()

    # Get key (optional parameter)
    key = arguments.get("key")

    if not items:
        return {"sorted_items": [], "count": 0, "order": order}

    # Auto-detect numeric key if items are dicts and no key specified
    first_item = items[0]
    if key is None and isinstance(first_item, dict):
        for k in first_item.keys():
            if isinstance(first_item[k], (int, float)):
                key = k
                break

    try:
        # Sort based on whether items are dicts and if key is provided
        if key and all(isinstance(item, dict) for item in items):
            sorted_items = sorted(items, key=lambda x: x.get(key, 0), reverse=(order == "desc"))
        else:
            sorted_items = sorted(items, reverse=(order == "desc"))

        return {
            "sorted_items": sorted_items,
            "count": len(sorted_items),
            "order": order
        }
    except Exception as e:
        return {
            "sorted_items": items,
            "count": len(items),
            "error": f"Failed to sort: {str(e)}"
        }
