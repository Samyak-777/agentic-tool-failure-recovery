TOOL_NAME = "get_contact_info_hris"

from tools.plugins import get_contact_info as gci

ALTERNATIVE_TOOLS = gci.ALTERNATIVE_TOOLS
CONSTRAINTS = gci.CONSTRAINTS



def execute(arguments, context) -> dict:
    """Retrieve contact info using an HRIS-style provider."""
    name = arguments.get("name")
    if not name:
        return {"error": "Name parameter is required"}

    if hasattr(context, "find_alternative_output"):
        existing = context.find_alternative_output(
            ALTERNATIVE_TOOLS,
            {"name": name},
        )
        if existing:
            return existing

    return gci._build_contact_result(name)
