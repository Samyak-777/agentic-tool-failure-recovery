"""Unit tests for SchemaChecker (L1)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.schema_checker import SchemaChecker
from semantic_validation.schema.extractor import SchemaExtractor
from semantic_validation.core.status import CheckerStatus
from semantic_validation.tests.fixtures.mock_outputs import MockToolLoader


@pytest.fixture
def checker():
    loader = MockToolLoader()
    extractor = SchemaExtractor(loader)
    return SchemaChecker(extractor)


def test_schema_valid(checker):
    output = {"temperature_celsius": 22, "condition": "Sunny"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.VALID
    assert "2 fields verified" in res.reason


def test_schema_missing_field(checker):
    output = {"condition": "Sunny"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "temperature_celsius" in res.reason


def test_schema_not_a_dict(checker):
    res = checker.check("get_weather_openweather", {}, "string output")
    assert res.status == CheckerStatus.INVALID


def test_schema_tool_error_not_applicable(checker):
    output = {"error": "API rate limited"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.NOT_APPLICABLE


def test_schema_no_schema_defined(checker):
    output = {"foo": "bar"}
    res = checker.check("no_schema_tool", {}, output)
    assert res.status == CheckerStatus.NOT_APPLICABLE
