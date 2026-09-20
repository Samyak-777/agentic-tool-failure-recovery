"""
get_news_newsapi Tool Plugin

Function: Get latest news headlines using NewsAPI.org
Category: Source
Domain: General
"""

TOOL_NAME = "get_news_newsapi"

# 可替换工具组
ALTERNATIVE_TOOLS = [
    "get_news_newsapi",
    "get_news_gnews",
    "get_news_currents",
    "get_news_reuters",
    "get_news_ap"
]

# Deterministic mapping of category -> news headlines
CASES = {
    "technology": {
        "category": "technology",
        "headlines": [
            "AI breakthrough in natural language processing",
            "New quantum computer achieves major milestone",
            "Tech giant announces revolutionary chip design"
        ],
        "count": 3
    },
    "business": {
        "category": "business",
        "headlines": [
            "Global markets reach new highs",
            "Major merger announced in tech sector",
            "Economic growth exceeds expectations"
        ],
        "count": 3
    },
    "sports": {
        "category": "sports",
        "headlines": [
            "Olympic champion breaks world record",
            "Major upset in championship finals",
            "New stadium project approved"
        ],
        "count": 3
    },
    "health": {
        "category": "health",
        "headlines": [
            "New vaccine shows promising results",
            "Study reveals benefits of daily exercise",
            "Medical breakthrough in cancer treatment"
        ],
        "count": 3
    },
}
DEFAULT = {
    "category": "general",
    "headlines": [
        "Breaking news update",
        "Important development reported",
        "Latest updates available"
    ],
    "count": 3
}

CONSTRAINTS = {
    "category": list(CASES.keys())
}


def execute(arguments, context) -> dict:
    """
    Get news headlines by category

    Args:
        arguments: Tool parameters
            - category (str): News category (technology, business, sports, health)
        context: ExecutionContext，可访问前序工具输出

    Returns:
        dict: Dictionary containing news headlines
    """
    category = (arguments.get("category") or "").lower()

    # 检查是否已查询过该类别的新闻（任何替代工具）
    if hasattr(context, 'find_alternative_output'):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"category": category}
        )
        if existing:
            return existing

    return dict(CASES.get(category, DEFAULT))
