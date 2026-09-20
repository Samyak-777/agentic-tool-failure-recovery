"""
browse_storage Tool Plugin

Function: List files in a cloud storage folder
Category: Source
Domain: Office
"""

TOOL_NAME = "browse_storage"

CONSTRAINTS = {
    "folder_path": ["/projects", "/projects/report", "/personal"],
    "extension": [".docx", ".pdf", ".xlsx", ".txt"]
}

# Hardcoded File System
FILE_SYSTEM = {
    "/projects": [
        {"name": "Project_Alpha_Plan.docx", "size": 2.5, "type": ".docx", "owner": "alice"},
        {"name": "Q3_Report_Draft.pdf", "size": 4.1, "type": ".pdf", "owner": "bob"},
    ],
    "/projects/report": [
        {"name": "Financial_Overview.xlsx", "size": 1.2, "type": ".xlsx", "owner": "charlie"},
        {"name": "Executive_Summary.docx", "size": 0.8, "type": ".docx", "owner": "alice"},
    ],
    "/personal": [
        {"name": "Resume.pdf", "size": 0.5, "type": ".pdf", "owner": "user"},
        {"name": "Notes.txt", "size": 0.1, "type": ".txt", "owner": "user"},
    ]
}

def execute(arguments, context) -> dict:
    # Get folder_path (required parameter)
    folder_path = arguments.get("folder_path")
    if not folder_path:
        return {"error": "folder_path is required"}

    # Get extension (optional parameter)
    extension = arguments.get("extension") or ""
    if extension:
        extension = extension.lower()

    # Normalize path (remove trailing slash)
    path = folder_path.rstrip("/")
    if path == "": path = "/"

    files = FILE_SYSTEM.get(path)

    if files is None:
        return {
            "found": False, 
            "error": f"Folder '{folder_path}' not found.",
            "available_folders": list(FILE_SYSTEM.keys())
        }

    # Filter by extension if provided
    filtered_files = []
    for f in files:
        if extension and not f["name"].lower().endswith(extension):
            continue
        filtered_files.append(f)

    return {
        "found": True,
        "folder": folder_path,
        "total_count": len(files),
        "matched_count": len(filtered_files),
        "files": filtered_files
    }