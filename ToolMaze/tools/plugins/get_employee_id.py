"""
get_employee_id Tool Plugin

Function: Retrieve user id for a person
Category: Source
Domain: Office
"""

TOOL_NAME = "get_employee_id"

CONSTRAINTS = {
    "name": ["alice", "bob", "charlie", "david"]
}

# Hardcoded contact directory
CONTACTS = {
    "alice": {"email": "alice@company.com", "phone": "+1-555-0101", "department": "Engineering", "user_id": "u_alice"},
    "bob": {"email": "bob@company.com", "phone": "+1-555-0102", "department": "Product", "user_id": "u_bob"},
    "charlie": {"email": "charlie@company.com", "phone": "+1-555-0103", "department": "Design", "user_id": "u_charlie"},
    "david": {"email": "david@company.com", "phone": "+1-555-0104", "department": "Marketing", "user_id": "u_david"},
}

def execute(arguments, context) -> dict:
    """
    Get contact details (Mock implementation)
    """
    # 只验证真正必填的参数（required: ["name"]）
    name = arguments.get("name")

    if not name:
        return {"error": "Name parameter is required"}

    name = name.lower()

    # Simple exact match or partial match logic
    contact = CONTACTS.get(name)
    
    if not contact:
        # Fallback partial search
        for key, val in CONTACTS.items():
            if name in key:
                contact = val
                name = key # normalize name
                break
    
    if not contact:
        return {
            "found": False,
            "error": f"Contact '{name}' not found."
        }

    return {
        "status": "success",
        "department": contact["department"],
        "user_id": contact["user_id"]
    }