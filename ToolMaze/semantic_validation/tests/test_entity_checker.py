"""Unit tests for EntityChecker (L6)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.entity_checker import EntityChecker
from semantic_validation.core.status import CheckerStatus


def test_entity_match_valid():
    checker = EntityChecker()
    args = {"city": "Tokyo"}
    result = {"city": "Tokyo", "temperature_celsius": 22}
    res = checker.check("get_weather_openweather", args, result)
    assert res.status == CheckerStatus.VALID


def test_entity_mismatch_p3_detection():
    checker = EntityChecker()
    args = {"city": "Tokyo"}
    result = {"city": "Osaka", "temperature_celsius": 22}
    res = checker.check("get_weather_openweather", args, result)
    assert res.status == CheckerStatus.INVALID
    assert "Requested city='Tokyo', but output returned city='Osaka'" in res.reason


def test_no_entity_field_not_applicable():
    checker = EntityChecker()
    args = {"city": "Tokyo"}
    result = {"temperature_celsius": 22}  # No city field returned
    res = checker.check("get_weather_openweather", args, result)
    assert res.status == CheckerStatus.NOT_APPLICABLE
