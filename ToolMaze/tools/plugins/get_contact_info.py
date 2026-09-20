"""
get_contact_info Tool Plugin

Function: Retrieve contact details for a person
Category: Source
Domain: Office
"""

TOOL_NAME = "get_contact_info"

ALTERNATIVE_TOOLS = [
    "get_contact_info",
    "get_contact_info_directory",
    "get_contact_info_hris",
    "get_contact_info_crm",
]

CONSTRAINTS = {
    "name": ["alice", "bob", "charlie", "david"]
}

CONTACTS = {
    "alice": {
        "email": "alice@company.com",
        "phone": "+1-555-0101",
        "department": "Engineering",
        "user_id": "u_alice",
    },
    "bob": {
        "email": "bob@company.com",
        "phone": "+1-555-0102",
        "department": "Product",
        "user_id": "u_bob",
    },
    "charlie": {
        "email": "charlie@company.com",
        "phone": "+1-555-0103",
        "department": "Design",
        "user_id": "u_charlie",
    },
    "david": {
        "email": "david@company.com",
        "phone": "+1-555-0104",
        "department": "Marketing",
        "user_id": "u_david",
    },
}


def _lookup_contact(name):
    query = (name or "").lower()
    if not query:
        return "", None

    contact = CONTACTS.get(query)
    normalized_name = query

    if not contact:
        for key, value in CONTACTS.items():
            if query in key:
                normalized_name = key
                contact = value
                break

    return normalized_name, contact



def _build_contact_result(name):
    normalized_name, contact = _lookup_contact(name)

    if not contact:
        return {
            "found": False,
            "error": f"Contact '{(name or '').lower()}' not found.",
        }

    return {
        "found": True,
        "name": normalized_name.capitalize(),
        "email": contact["email"],
        "phone": contact["phone"],
        "department": contact["department"],
        "user_id": contact["user_id"],
    }



def execute(arguments, context) -> dict:
    """Get contact details (mock implementation)."""
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

    return _build_contact_result(name)
