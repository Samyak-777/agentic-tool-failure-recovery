
from dag_rerouting.execution_controller import ExecutionController


def test_c1_uses_execution_trace():
    task_json = {
        "execution_trace": [
            {"tool_name": "search"},
            {"tool_name": "get_details"},
            {"tool_name": "summarize"},
        ]
    }

    controller = ExecutionController(task_json)

    assert controller.get_next_tool([]) == "search"
    assert controller.get_next_tool(["search"]) == "get_details"
    assert controller.get_next_tool(
        ["search", "get_details"]
    ) == "summarize"


def test_c2_c4_uses_valid_paths():
    task_json = {
        "valid_paths": [
            {"tools": ["search", "verify", "summarize"]},
            {"tools": ["database_lookup", "verify", "summarize"]},
        ]
    }

    controller = ExecutionController(task_json)

    assert controller.get_next_tool([]) == "search"
    assert controller.get_next_tool(
        ["database_lookup"]
    ) == "verify"


def test_controller_does_not_repeat_executed_tools():
    task_json = {
        "valid_paths": [
            {"tools": ["search", "filter", "summarize"]}
        ]
    }

    controller = ExecutionController(task_json)

    assert controller.get_next_tool(
        ["search", "filter"]
    ) == "summarize"


def test_controller_returns_none_when_path_is_complete():
    task_json = {
        "valid_paths": [
            {"tools": ["search", "summarize"]}
        ]
    }

    controller = ExecutionController(task_json)

    assert controller.get_next_tool(
        ["search", "summarize"]
    ) is None


def test_controller_supports_list_format_paths():
    task_json = {
        "valid_paths": [
            ["search", "verify", "summarize"]
        ]
    }

    controller = ExecutionController(task_json)

    assert controller.get_next_tool([]) == "search"
    assert controller.get_next_tool(
        ["search"]
    ) == "verify"
