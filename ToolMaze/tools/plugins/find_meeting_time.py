"""
find_meeting_time Tool Plugin

Function: Find a common time slot for multiple users
Category: Processor
Domain: Office
"""
OFFICE_MOCK_DATA = {
    "users": {
        "alice": {"email": "alice@example.com", "id": "u_alice"},
        "bob": {"email": "bob@example.com", "id": "u_bob"},
        "charlie": {"email": "charlie@example.com", "id": "u_charlie"},
        "david": {"email": "david@example.com", "id": "u_david"}
    },
    "calendar": {
        "u_alice":   {"2024-10-24": ["09:00", "10:00", "14:00", "15:00"]},
        "u_bob":     {"2024-10-24": ["10:00", "11:00", "14:00", "16:00"]},
        "u_charlie": {"2024-10-24": ["09:00", "14:00", "15:00", "16:00"]},
        "u_david":   {"2024-10-24": ["09:00", "10:00", "14:00", "16:00"]}
    }
}
TOOL_NAME = "find_meeting_time"

CONSTRAINTS = {
    "user_ids": [["u_alice", "u_bob"], ["u_alice", "u_charlie"], ["u_bob", "u_david"], ["u_alice", "u_bob", "u_charlie"]],
    "preferred_date": ["2024-10-24"]
}

def execute(arguments, context) -> dict:
    # Get user_ids (required parameter)
    user_ids = arguments.get("user_ids")
    if not user_ids or not isinstance(user_ids, list) or len(user_ids) == 0:
        return {"error": "user_ids list is required"}

    # Get duration_minutes (optional parameter with reasonable default)
    duration_minutes = arguments.get("duration_minutes") or 60

    # Get preferred_date (optional parameter)
    preferred_date = arguments.get("preferred_date")

    # Use preferred_date as date
    date = preferred_date

    # Mock Logic:
    # Deterministically calculate a "common" slot based on the date hash.
    # This simulates that the processor has checked everyone's calendar.
    user_ids = list(set(user_ids))
    first_user_id = user_ids[0]
    if not first_user_id in OFFICE_MOCK_DATA["calendar"]:
        return {"error": f"User ID '{first_user_id}' not found"}
    user_cal = OFFICE_MOCK_DATA["calendar"].get(first_user_id, {})
    # Get slots for the specific date, default to empty set if date not found
    common_slots = set(user_cal.get(date, []))

    # 2. Iterate through the rest of the users and find the intersection
    for uid in user_ids[1:]:
        if not uid in OFFICE_MOCK_DATA["calendar"]:
            return {"error": f"User ID '{uid}' not found"}
        u_cal = OFFICE_MOCK_DATA["calendar"].get(uid, {})
        u_slots = set(u_cal.get(date, []))

        # Intersect current common slots with this user's slots
        common_slots.intersection_update(u_slots)

        # Optimization: If common slots are already empty, stop checking
        if not common_slots:
            break

    # 3. 过滤掉已预订的时间段（从 context.history 中）
    if hasattr(context, 'history'):
        for record in context.history:
            if record.tool_name == "schedule_meeting" and "error" not in record.output:
                meeting_date = record.output.get("date") or record.arguments.get("date")
                meeting_start = record.output.get("start_time") or record.arguments.get("start_time")
                if meeting_date == date and meeting_start:
                    # 提取时间部分
                    if " " in meeting_start:
                        meeting_start = meeting_start.split(" ")[1]
                    # 从可用时间段中移除
                    common_slots.discard(meeting_start)
    
    if not common_slots:
        return {
            "status": "failed",
            "message": f"No common slot found on {date} for the specified users.",
            "users_checked": user_ids,
            "date": date
        }

    # 3. Select the best slot (e.g., the earliest one)
    sorted_slots = sorted(list(common_slots))
    start_time = sorted_slots[0]

    # 4. Calculate end time based on duration
    # Parse HH:MM
    try:
        h, m = map(int, start_time.split(':'))
        total_minutes = h * 60 + m + duration_minutes
        end_h = total_minutes // 60
        end_m = total_minutes % 60
        end_time = f"{end_h:02d}:{end_m:02d}"
    except ValueError:
        # Fallback if time format is unexpected
        end_time = "Unknown"
    

    return {
        "status": "success",
        "date": date,
        "users_checked": user_ids,
        "duration_minutes": duration_minutes,
        "recommended_slot": {
            "start_time": start_time,
            "end_time": end_time
        },
        "message": f"Found common slot on {date} at {start_time}"
    }