TOOL_NAME = "get_recommendations_trending"

from tools.plugins import get_recommendations as gr

ALTERNATIVE_TOOLS = gr.ALTERNATIVE_TOOLS
CONSTRAINTS = gr.CONSTRAINTS


def execute(arguments, context) -> dict:
    """Retrieve recommendations using a trending-products provider."""
    raw_product_id = arguments.get("product_id")
    raw_category = arguments.get("category")
    raw_user_id = arguments.get("user_id")

    if hasattr(context, "find_alternative_output"):
        args_match = {}
        if raw_product_id is not None:
            args_match["product_id"] = raw_product_id
        if raw_category is not None:
            args_match["category"] = raw_category
        if raw_user_id is not None:
            args_match["user_id"] = raw_user_id
        if args_match:
            existing = context.find_alternative_output(ALTERNATIVE_TOOLS, args_match)
            if existing:
                return existing

    category = raw_category or "all"
    user_id = raw_user_id or "default_user"
    return gr._build_recommendations_result(raw_product_id, category, user_id, context)
