import sys
from pathlib import Path

import pytest

TOOLMAZE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLMAZE_ROOT))

from evaluation.core.judge import JudgeSystem


def make_task():
    """Minimal C3/P2 task with two complete alternative paths."""
    path0 = [
        "get_iot_device_status",
        "get_light_mesh_snapshot_native",
        "archive_light_mesh_snapshot_native",
        "analyze_text",
        "get_light_status",
        "snapshot_workspace",
    ]
    path1 = [
        "get_iot_device_status",
        "get_light_bridge_payload_native",
        "archive_light_bridge_payload_native",
        "analyze_text",
        "get_light_status",
        "snapshot_workspace",
    ]

    def steps(tools, victim=None):
        return [
            {
                "step": i + 1,
                "tool_name": tool,
                "is_perturbed": tool == victim,
            }
            for i, tool in enumerate(tools)
        ]

    return {
        "task_id": "C3_task_005",
        "complexity": "C3",
        "perturbation_mode": "P2",
        "valid_paths": [
            {
                "path_id": "path_0",
                "tools": path0,
                "execution_trace": steps(path0, "get_light_mesh_snapshot_native"),
            },
            {
                "path_id": "path_1",
                "tools": path1,
                "execution_trace": steps(path1, "get_light_bridge_payload_native"),
            },
        ],
        "alternative_tools": [
            "get_light_mesh_snapshot_native",
            "archive_light_mesh_snapshot_native",
            "get_light_bridge_payload_native",
            "archive_light_bridge_payload_native",
        ],
    }


def make_trace(calls):
    """Build the message format consumed by JudgeSystem."""
    messages = []

    for i, (tool, output) in enumerate(calls, start=1):
        call_id = f"call_{i}"
        messages.append({
            "role": "assistant",
            "type": "tool_call",
            "tool_call": {
                "id": call_id,
                "name": tool,
                "arguments": {},
            },
        })
        messages.append({
            "role": "tool",
            "type": "tool_result",
            "tool_call_id": call_id,
            "name": tool,
            "content": output,
        })

    messages.append({
        "role": "assistant",
        "type": "final_answer",
        "content": "Task completed successfully." if calls and calls[-1][0] == "snapshot_workspace"
        else "The requested operation could not be completed because the tool failed.",
    })
    return {"messages": messages}


def test_c3_p2_stopping_at_failed_victim_is_task_failure():
    task = make_task()
    trace = make_trace([
        ("get_iot_device_status", {"power_state": "off"}),
        ("get_light_mesh_snapshot_native", {"error": "Account Quota Exhausted"}),
    ])

    result = JudgeSystem().judge(task, trace)

    assert result["pass"] is False


def test_c3_p2_successful_alternative_path_passes():
    task = make_task()
    trace = make_trace([
        ("get_iot_device_status", {"power_state": "off"}),
        ("get_light_mesh_snapshot_native", {"error": "Account Quota Exhausted"}),
        ("get_light_bridge_payload_native", {"bridge_state": "off"}),
        ("archive_light_bridge_payload_native", {"status": "archived"}),
        ("analyze_text", {"raw_content": "bridge_light_archive_native"}),
        ("get_light_status", {"power_state": "off"}),
        ("snapshot_workspace", {"status": "completed", "backup_name": "weekly_iot_backup"}),
    ])

    result = JudgeSystem().judge(task, trace)
    print("\nJUDGE RESULT:", result)
    assert result["pass"] is True
    assert "path_1" in result["trace_check"]["matched_paths"]
    assert "path_1" in result["trace_check"]["switched_paths"]
