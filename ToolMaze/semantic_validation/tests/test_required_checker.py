"""Unit tests for RequiredFieldChecker (L3)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.required_checker import RequiredFieldChecker
from semantic_validation.schema.extractor import SchemaExtractor
from semantic_validation.core.status import CheckerStatus
from semantic_validation.tests.fixtures.mock_outputs import MockToolLoader


@pytest.fixture
def checker():
    loader = MockToolLoader()
    extractor = SchemaExtractor(loader)
    return RequiredFieldChecker(extractor)


def test_required_fields_present_and_not_none(checker):
    output = {"temperature_celsius": 18, "condition": "Cloudy"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.VALID


def test_required_field_is_none(checker):
    output = {"temperature_celsius": None, "condition": "Cloudy"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "null: ['temperature_celsius']" in res.reason


def test_required_field_missing(checker):
    output = {"condition": "Cloudy"}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "missing: ['temperature_celsius']" in res.reason
