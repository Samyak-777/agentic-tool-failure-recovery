"""Unit tests for TemporalChecker (L5)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.temporal_checker import TemporalChecker
from semantic_validation.config.validation_config import TemporalConfig
from semantic_validation.core.status import CheckerStatus


def test_valid_iso_timestamp():
    checker = TemporalChecker()
    output = {"created_at": "2026-09-27T10:00:00Z"}
    res = checker.check("any_tool", {}, output)
    assert res.status == CheckerStatus.VALID


def test_malformed_timestamp():
    checker = TemporalChecker()
    output = {"created_at": "not-a-timestamp-1234"}
    res = checker.check("any_tool", {}, output)
    assert res.status == CheckerStatus.INVALID
    assert "Malformed timestamp" in res.reason


def test_no_temporal_fields_not_applicable():
    checker = TemporalChecker()
    output = {"price_usd": 100}
    res = checker.check("any_tool", {}, output)
    assert res.status == CheckerStatus.NOT_APPLICABLE
