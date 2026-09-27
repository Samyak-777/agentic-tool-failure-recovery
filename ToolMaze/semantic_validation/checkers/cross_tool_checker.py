"""
semantic_validation/checkers/cross_tool_checker.py

Checker 9 (L9): Cross-Tool Consistency Checker.

Validates inter-tool dependencies and consistency across tool calls in the
execution history using explicit rules and context.history.

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If no cross-tool rules apply: NOT_APPLICABLE.
    - If a cross-tool rule fails: INVALID.
    - If all rules pass: VALID.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..rules.cross_tool_rules import get_cross_tool_rules_for_tool, CrossToolRule
from .base import BaseChecker


class CrossToolChecker(BaseChecker):
    """L9: Checks consistency across sequential tool interactions in execution history."""

    name: str = "cross_tool"

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
                reason="Tool returned an explicit error response; cross-tool checks do not apply",
                details={"error": str(result.get("error"))},
            )

        rules: List[CrossToolRule] = get_cross_tool_rules_for_tool(tool_name)
        if not rules:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No cross-tool consistency rules apply to '{tool_name}'",
                details={"tool_name": tool_name},
            )

        violations: List[Dict[str, Any]] = []
        applied_rules: List[str] = []

        for rule in rules:
            applied_rules.append(rule.rule_id)
            passed, failure_msg = rule.check(tool_name, arguments, result, context)
            if not passed:
                violations.append({
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "reason": failure_msg,
                    "source": rule.source,
                })

        if violations:
            reasons = [f"[{v['rule_id']}] {v['reason']}" for v in violations]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="Cross-tool consistency failure: " + "; ".join(reasons),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "applied_rules": applied_rules,
                },
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"Cross-tool consistency confirmed ({len(applied_rules)} rule(s) checked)",
            details={
                "tool_name": tool_name,
                "applied_rules": applied_rules,
            },
        )
