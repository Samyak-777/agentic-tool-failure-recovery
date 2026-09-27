"""
semantic_validation/checkers/cross_field_checker.py

Checker 7 (L7): Cross-Field Rule Checker.

Evaluates intra-output invariant constraints between multiple fields
(e.g., free_slots <= total_slots, start_time < end_time, check_in < check_out).

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If no cross-field rules apply to this tool's output fields: NOT_APPLICABLE.
    - If any cross-field constraint fails: INVALID.
    - Otherwise: VALID.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..rules.cross_field_rules import get_cross_field_rules_for_tool, CrossFieldRule
from .base import BaseChecker


class CrossFieldChecker(BaseChecker):
    """L7: Validates relational constraints across fields within the same tool output."""

    name: str = "cross_field"

    def check(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        state: Optional[ExecutionValidationState] = None,
        context: Optional[Any] = None,
    ) -> CheckResult:
        if not isinstance(result, dict):
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason=f"Tool output must be a dict, got {type(result).__name__}",
                details={"actual_type": type(result).__name__},
            )

        if "error" in result:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason="Tool returned an explicit error response; cross-field checks do not apply",
                details={"error": str(result.get("error"))},
            )

        rules: List[CrossFieldRule] = get_cross_field_rules_for_tool(tool_name, result)
        if not rules:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No applicable cross-field rules for tool '{tool_name}'",
                details={"tool_name": tool_name},
            )

        violations: List[Dict[str, Any]] = []
        applied_rules: List[str] = []

        for rule in rules:
            applied_rules.append(rule.rule_id)
            passed, failure_msg = rule.check(result)
            if not passed:
                violations.append({
                    "rule_id": rule.rule_id,
                    "fields_involved": rule.fields_involved,
                    "description": rule.description,
                    "failure_reason": failure_msg,
                    "source": rule.source,
                })

        if violations:
            msgs = [f"[{v['rule_id']}] {v['failure_reason']}" for v in violations]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="Cross-field rule violation: " + "; ".join(msgs),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "applied_rules": applied_rules,
                },
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"All {len(applied_rules)} cross-field rule(s) satisfied",
            details={
                "tool_name": tool_name,
                "applied_rules": applied_rules,
            },
        )
