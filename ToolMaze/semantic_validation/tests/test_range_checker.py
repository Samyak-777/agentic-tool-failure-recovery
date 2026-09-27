"""Unit tests for RangeChecker (L4)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.range_checker import RangeChecker
from semantic_validation.schema.range_registry import RangeRegistry
from semantic_validation.core.status import CheckerStatus


@pytest.fixture
def checker():
    registry = RangeRegistry()
    return RangeChecker(registry)


def test_positive_stock_price_valid(checker):
    output = {"price_usd": 150.25, "currency": "USD"}
    res = checker.check("get_stock_yahoo_finance", {}, output)
    assert res.status == CheckerStatus.VALID


def test_negative_stock_price_invalid(checker):
    output = {"price_usd": -10.0, "currency": "USD"}
    res = checker.check("get_stock_yahoo_finance", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "RR-001" in res.reason


def test_zero_stock_price_invalid(checker):
    output = {"price_usd": 0.0, "currency": "USD"}
    res = checker.check("get_stock_yahoo_finance", {}, output)
    assert res.status == CheckerStatus.INVALID


def test_total_slots_non_negative_valid(checker):
    output = {"total_slots": 0}
    res = checker.check("query_availability", {}, output)
    assert res.status == CheckerStatus.VALID


def test_total_slots_negative_invalid(checker):
    output = {"total_slots": -1}
    res = checker.check("query_availability", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "RR-004" in res.reason


def test_unregistered_tool_not_applicable(checker):
    output = {"temperature_celsius": 22}
    res = checker.check("get_weather_openweather", {}, output)
    assert res.status == CheckerStatus.NOT_APPLICABLE
