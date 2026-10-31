
import pytest

from dag_rerouting.prerequisite_checker import PrerequisiteChecker


@pytest.fixture
def task_json():
    return {
        "task_id": "test_task",
        "valid_paths": [
            {
                "path_id": "path_1",
                "tools": [
                    "get_contact",
                    "query_calendar",
                    "send_email",
                ],
            },
            {
                "path_id": "path_2",
                "tools": [
                    "get_contact",
                    "query_calendar_alternative",
                    "send_email",
                ],
            },
        ],
    }


def test_first_prerequisite_missing(task_json):
    checker = PrerequisiteChecker(task_json)

    result = checker.check(
        requested_tool="query_calendar",
        executed_tools=set(),
    )

    assert result["allowed"] is False
    assert result["missing_prerequisites"] == ["get_contact"]


def test_multiple_prerequisites_missing():
    task = {
        "valid_paths": [
            {
                "path_id": "path_1",
                "tools": [
                    "get_contact",
                    "query_calendar",
                    "send_email",
                ],
            }
        ]
    }

    checker = PrerequisiteChecker(task)

    result = checker.check(
        requested_tool="send_email",
        executed_tools=set(),
    )

    assert result["allowed"] is False
    assert result["missing_prerequisites"] == [
        "get_contact",
        "query_calendar",
    ]


def test_alternative_path_already_satisfied(task_json):
    checker = PrerequisiteChecker(task_json)

    result = checker.check(
        requested_tool="query_calendar_alternative",
        executed_tools={"get_contact"},
    )

    assert result["allowed"] is True
    assert result["missing_prerequisites"] == []


def test_no_valid_paths():
    checker = PrerequisiteChecker({})

    result = checker.check(
        requested_tool="some_tool",
        executed_tools=set(),
    )

    assert result["allowed"] is True
    assert result["missing_prerequisites"] == []


def test_requested_tool_not_in_any_path(task_json):
    checker = PrerequisiteChecker(task_json)

    result = checker.check(
        requested_tool="unknown_tool",
        executed_tools=set(),
    )

    assert result["allowed"] is False
    assert result["missing_prerequisites"] == []
    assert "not present" in result["reason"]


def test_all_prerequisites_already_executed(task_json):
    checker = PrerequisiteChecker(task_json)

    result = checker.check(
        requested_tool="send_email",
        executed_tools={
            "get_contact",
            "query_calendar",
        },
    )

    assert result["allowed"] is True
    assert result["missing_prerequisites"] == []


def test_one_valid_path_is_enough():
    task = {
        "valid_paths": [
            {
                "path_id": "path_1",
                "tools": ["get_contact", "query_calendar"],
            },
            {
                "path_id": "path_2",
                "tools": ["query_calendar"],
            },
        ]
    }

    checker = PrerequisiteChecker(task)

    result = checker.check(
        requested_tool="query_calendar",
        executed_tools=set(),
    )

    assert result["allowed"] is True
    assert result["missing_prerequisites"] == []


def test_empty_executed_tools(task_json):
    checker = PrerequisiteChecker(task_json)

    result = checker.check("get_contact")

    assert result["allowed"] is True


def test_invalid_path_entry_is_ignored():
    task = {
        "valid_paths": [
            None,
            {"path_id": "bad_path", "tools": "not_a_list"},
            {
                "path_id": "valid_path",
                "tools": ["get_contact", "query_calendar"],
            },
        ]
    }

    checker = PrerequisiteChecker(task)

    result = checker.check(
        requested_tool="query_calendar",
        executed_tools={"get_contact"},
    )

    assert result["allowed"] is True
