"""
send_email Tool Plugin

Function: Send email (simulated)
Category: Action
Domain: Office
"""

TOOL_NAME = "send_email"


def execute(arguments, context) -> dict:
    """
    Send email (simulation - no actual email sent)

    Args:
        arguments: Tool parameters
            - recipients (list): List of recipient email addresses
            - subject (str): Email subject
            - body (str): Email body

    Returns:
        dict: Dictionary containing send status
    """
    recipients = arguments.get("recipients")
    if not recipients:
        return {
            "error": "Recipients are required. Please provide email recipients."
        }

    subject = arguments.get("subject") or "(No Subject)"

    body = arguments.get("body")

    if not body:
        return {
            "error": "Email body is required"
        }

    # Validate recipients format
    if not isinstance(recipients, list):
        recipients = [recipients]

    # Simulate sending
    return {
        "status": "sent",
        "message": f"Email sent successfully to {len(recipients)} recipient(s)",
        "recipients": recipients,
        "subject": subject,
        "body_length": len(body)
    }
