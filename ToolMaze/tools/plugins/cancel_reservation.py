"""
cancel_reservation Tool Plugin

Function: Cancel a travel booking (simulated)
Category: Action
Domain: Travel
"""

TOOL_NAME = "cancel_reservation"


def execute(arguments, context) -> dict:
    """
    Cancel booking (simulation)

    Args:
        arguments: Tool parameters
            - booking_id (str): Booking ID to cancel
            - reason (str, optional): Cancellation reason

    Returns:
        dict: Dictionary containing cancellation status
    """
    # Get booking_id (required parameter)
    booking_id = arguments.get("booking_id")
    if not booking_id:
        return {
            "error": "Booking ID is required"
        }

    # Get reason (optional parameter)
    reason = arguments.get("reason") or ""

    # Get refund amount from arguments, fallback to deterministic generation
    refund_amount = arguments.get("refund_amount")

    if not refund_amount:
        refund_amount = 350

    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking_id,
        "cancellation_reason": reason if reason else "User requested",
        "refund_amount": refund_amount,
        "refund_currency": "USD",
        "status": "cancelled"
    }
