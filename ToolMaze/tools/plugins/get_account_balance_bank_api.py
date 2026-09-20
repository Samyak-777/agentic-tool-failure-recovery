TOOL_NAME = "get_account_balance_bank_api"

from tools.plugins import get_account_balance as gab

ALTERNATIVE_TOOLS = gab.ALTERNATIVE_TOOLS
CONSTRAINTS = gab.CONSTRAINTS


def execute(arguments, context) -> dict:
    """获取账户余额（Bank API）"""
    return gab.execute(arguments, context)
