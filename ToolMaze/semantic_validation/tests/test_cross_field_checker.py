"""Unit tests for CrossFieldChecker (L7)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.cross_field_checker import CrossFieldChecker
from semantic_validation.core.status import CheckerStatus


def test_cross_field_free_slots_valid():
    checker = CrossFieldChecker()
    output = {"total_slots": 3, "free_slots": ["09:00", "10:00"]}
    res = checker.check("query_availability", {}, output)
    assert res.status == CheckerStatus.VALID


def test_cross_field_free_slots_exceeds_total():
    checker = CrossFieldChecker()
    output = {"total_slots": 1, "free_slots": ["09:00", "10:00", "11:00"]}
    res = checker.check("query_availability", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "CFR-001" in res.reason


def test_cross_field_start_end_time():
    checker = CrossFieldChecker()
    valid_output = {"start_time": "09:00", "end_time": "10:00"}
    assert checker.check("any_tool", {}, valid_output).status == CheckerStatus.VALID

    invalid_output = {"start_time": "11:00", "end_time": "10:00"}
    res_bad = checker.check("any_tool", {}, invalid_output)
    assert res_bad.status == CheckerStatus.INVALID
    assert "CFR-002" in res_bad.reason
