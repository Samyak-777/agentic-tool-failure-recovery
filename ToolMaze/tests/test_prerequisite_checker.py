
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


def test_execution_trace_c1_extraction():
    task = {
        "task_id": "C1_task_001_P0",
        "execution_trace": [
            {"step": 1, "tool_name": "get_flight_info"},
            {"step": 2, "tool_name": "build_flight_booking_request"},
            {"step": 3, "tool_name": "book_flight_with_status_check"},
            {"step": 4, "tool_name": "get_hotel_info_expedia"},
            {"step": 5, "tool_name": "book_hotel"},
        ],
    }
    checker = PrerequisiteChecker(task)
    assert len(checker.valid_paths) == 1
    assert checker.valid_paths[0]["tools"] == [
        "get_flight_info",
        "build_flight_booking_request",
        "book_flight_with_status_check",
        "get_hotel_info_expedia",
        "book_hotel",
    ]

    # Calling step 3 directly after step 1 should fail with missing step 2
    res = checker.check(
        requested_tool="book_flight_with_status_check",
        executed_tools={"get_flight_info"},
    )
    assert res["allowed"] is False
    assert res["missing_prerequisites"] == ["build_flight_booking_request"]

    # Calling step 2 after step 1 should be allowed
    res2 = checker.check(
        requested_tool="build_flight_booking_request",
        executed_tools={"get_flight_info"},
    )
    assert res2["allowed"] is True
    assert res2["missing_prerequisites"] == []


def test_valid_solution_paths_extraction():
    task = {
        "task_id": "task_sol",
        "valid_solution_paths": [
            ["tool_a", "tool_b", "tool_c"],
            ["tool_a", "tool_d", "tool_c"],
        ],
    }
    checker = PrerequisiteChecker(task)
    assert len(checker.valid_paths) == 2
    res = checker.check("tool_c", executed_tools={"tool_a"})
    assert res["allowed"] is False
    assert res["missing_prerequisites"] in [["tool_b"], ["tool_d"]]

    res2 = checker.check("tool_c", executed_tools={"tool_a", "tool_b"})
    assert res2["allowed"] is True
