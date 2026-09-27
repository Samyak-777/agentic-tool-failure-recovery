"""Unit tests for TypeChecker (L2)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.type_checker import TypeChecker
from semantic_validation.schema.extractor import SchemaExtractor
from semantic_validation.core.status import CheckerStatus
from semantic_validation.tests.fixtures.mock_outputs import MockToolLoader


@pytest.fixture
def checker():
    loader = MockToolLoader()
    extractor = SchemaExtractor(loader)
    return TypeChecker(extractor)


def test_type_valid(checker):
    output = {"temperature_celsius": 22, "condition": "Sunny"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.VALID


def test_type_mismatch_string_for_int(checker):
    output = {"temperature_celsius": "22", "condition": "Sunny"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "temperature_celsius" in res.reason


def test_type_mismatch_bool_for_int(checker):
    output = {"temperature_celsius": True, "condition": "Sunny"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "temperature_celsius" in res.reason


def test_type_array_element_validation(checker):
    output = {"total_slots": 5, "free_slots": ["10:00", "11:00"]}
    res = checker.check("query_availability", {}, output)
    assert res.status == CheckerStatus.VALID

    output_bad = {"total_slots": 5, "free_slots": ["10:00", 123]}
    res_bad = checker.check("query_availability", {}, output_bad)
    assert res_bad.status == CheckerStatus.INVALID
