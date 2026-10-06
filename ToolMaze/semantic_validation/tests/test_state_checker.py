"""Unit tests for StateChecker (L8)."""

try:
    import pytest
except ImportError:
    class _MockPytest:
        @staticmethod
        def fixture(fn):
            return fn
    pytest = _MockPytest()
from semantic_validation.checkers.state_checker import StateChecker
from semantic_validation.core.state_store import ExecutionValidationState
from semantic_validation.core.status import CheckerStatus


def test_state_entity_binding_consistency():
    checker = StateChecker()
    state = ExecutionValidationState(execution_id="exec-1", task_id="task-1")

    # Call 1: Alice bound to u_alice
    res1 = checker.check("get_contact_info", {"name": "Alice"}, {"user_id": "u_alice"}, state=state)
    assert res1.status == CheckerStatus.VALID

    # Call 2: Alice returning u_alice again
    res2 = checker.check("get_contact_info", {"name": "Alice"}, {"user_id": "u_alice"}, state=state)
    assert res2.status == CheckerStatus.VALID

    # Call 3: Alice suddenly returning u_bob (mutation violation!)
    res3 = checker.check("get_contact_info", {"name": "Alice"}, {"user_id": "u_bob"}, state=state)
    assert res3.status == CheckerStatus.INVALID
    assert "State mutation" in res3.reason
