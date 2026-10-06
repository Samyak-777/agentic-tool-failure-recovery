"""
semantic_validation/checkers/range_checker.py

Checker 4 (L4): Value Range Validation.

Validates that numeric output fields adhere to explicitly declared range constraints
from the RangeRegistry (e.g. stock/crypto prices > 0, exchange rates > 0, total_slots >= 0).

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If no range rules apply to this tool's output fields: NOT_APPLICABLE.
    - If any field violates a range rule: INVALID.
    - If all applicable rules pass: VALID.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..schema.range_registry import RangeRegistry, RangeRule
from .base import BaseChecker


class RangeChecker(BaseChecker):
    """L4: Validates numerical ranges against explicit registry rules."""

    name: str = "range"

    def __init__(self, range_registry: RangeRegistry) -> None:
        self.range_registry = range_registry

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
                reason="Tool returned an explicit error response; range checks do not apply",
                details={"error": str(result.get("error"))},
            )

        violations: List[Dict[str, Any]] = []
        applied_rules: List[str] = []

        for field_name, value in result.items():
            rules: List[RangeRule] = self.range_registry.get_rules(tool_name, field_name)
            for rule in rules:
                applied_rules.append(rule.rule_id)
                passed, failure_msg = rule.check(value)
                if not passed:
                    violations.append({
                        "rule_id": rule.rule_id,
                        "field_name": field_name,
                        "value": value,
                        "min_val": rule.min_val,
                        "max_val": rule.max_val,
                        "source": rule.source,
                        "message": failure_msg,
                    })

        if not applied_rules:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No range rules registered for tool '{tool_name}'",
                details={"tool_name": tool_name},
            )

        if violations:
            violation_msgs = [v["message"] for v in violations]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="Value range violation: " + "; ".join(violation_msgs),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "applied_rules": applied_rules,
                },
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"All {len(applied_rules)} range rule(s) satisfied for tool '{tool_name}'",
            details={
                "tool_name": tool_name,
                "applied_rules": applied_rules,
            },
        )
