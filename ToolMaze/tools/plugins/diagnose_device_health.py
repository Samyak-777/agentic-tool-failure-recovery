"""
diagnose_device_health Tool Plugin

Function: Analyze list of IoT devices to identify those with health issues
Category: Processor
Domain: IoT
"""

TOOL_NAME = "diagnose_device_health"

CONSTRAINTS = {
    "status_criteria": ["all_issues", "offline", "low_battery", "error"]
}

def execute(arguments, context) -> dict:
    """
    Filter devices based on status criteria.
    """
    # Get devices_data (from arguments)
    devices_data = arguments.get("devices_data") or []

    # Get status_criteria (optional parameter with reasonable default)
    criteria = arguments.get("status_criteria") or "all_issues"

    if not isinstance(devices_data, list):
        return {"error": "devices_data must be a list"}

    abnormal_devices = []
    
    for device in devices_data:
        if not isinstance(device, dict):
            continue
            
        issues = []
        
        # Check Offline
        if device.get("online_status") == "offline":
            issues.append("offline")
            
        # Check Low Battery (assuming threshold is 20%)
        batt = device.get("battery_level")
        if batt is not None and isinstance(batt, (int, float)) and batt < 20:
            issues.append("low_battery")
            
        # Check Errors
        if device.get("error_code"):
            issues.append("error")

        # Filtering Logic
        match = False
        if criteria == "all_issues" and len(issues) > 0:
            match = True
        elif criteria in issues:
            match = True
            
        if match:
            device_summary = {
                "device_id": device.get("device_id"),
                "type": device.get("type", "unknown"),
                "issues": issues
            }
            abnormal_devices.append(device_summary)
            
    return {
        "count": len(abnormal_devices),
        "status_criteria": criteria,
        "abnormal_devices": abnormal_devices
    }