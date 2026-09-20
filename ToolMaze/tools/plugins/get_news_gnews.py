TOOL_NAME = "get_news_gnews"

from tools.plugins import get_news_newsapi as gn

# 可替换工具组
ALTERNATIVE_TOOLS = gn.ALTERNATIVE_TOOLS

# GNews uses the same data structure as NewsAPI
CASES = gn.CASES
DEFAULT = gn.DEFAULT

CONSTRAINTS = {
    "category": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """获取新闻标题"""
    category = (arguments.get("category") or "").lower()

    # 检查是否已查询过该类别的新闻
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"category": category}
        )
        if existing:
            return existing

    return dict(CASES.get(category, DEFAULT))
