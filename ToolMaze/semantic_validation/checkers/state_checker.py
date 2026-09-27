"""
semantic_validation/checkers/state_checker.py

Checker 8 (L8): Accumulated State Consistency Checker.

Tracks state across calls within a single task execution (isolated via
ExecutionValidationState). Ensures entity bindings remain consistent throughout
the conversation (e.g., user_id for Alice cannot silently mutate to another ID).

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If state store is not provided: NOT_APPLICABLE.
    - If an established entity binding is contradicted by new output: INVALID.
    - Otherwise: VALID or NOT_APPLICABLE depending on whether state was checked.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from .base import BaseChecker


class StateChecker(BaseChecker):
    """L8: Maintains and verifies execution-scoped state consistency."""

    name: str = "state"

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
                reason="Tool returned an explicit error response; state checks do not apply",
                details={"error": str(result.get("error"))},
            )

        if state is None:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason="No active ExecutionValidationState available",
                details={"tool_name": tool_name},
            )

        step = len(state.observations) + 1
        violations: List[Dict[str, Any]] = []
        checked_bindings: List[str] = []

        # Check entity binding consistency: (name -> user_id, email, etc.)
        name_val = arguments.get("name") or arguments.get("person") or arguments.get("user")
        if name_val:
            name_canonical = str(name_val).strip().lower()
            for id_field in ("user_id", "email", "phone_number"):
                if id_field in result and result[id_field] is not None:
                    curr_val = str(result[id_field]).strip()
                    entity_key = f"{id_field}:{name_canonical}"
                    checked_bindings.append(entity_key)

                    prior = state.get_entity(entity_key)
                    if prior is not None:
                        prior_val, prior_step, prior_tool = prior
                        if prior_val != curr_val:
                            violations.append({
                                "entity_key": entity_key,
                                "name": name_canonical,
                                "field": id_field,
                                "current_value": curr_val,
                                "prior_value": prior_val,
                                "prior_step": prior_step,
                                "prior_tool": prior_tool,
                                "reason": (
                                    f"State mutation: '{entity_key}' was previously bound to "
                                    f"'{prior_val}' at step {prior_step} by '{prior_tool}', "
                                    f"now returned as '{curr_val}'"
                                ),
                            })
                    else:
                        state.register_entity(entity_key, curr_val, step, tool_name)

        # Record field observations for auditing
        for k, v in result.items():
            if isinstance(v, (str, int, float, bool)):
                state.record_observation(tool_name, k, v, step, arguments)

        if violations:
            state.flag_step(step)
            reasons = [v["reason"] for v in violations]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="State consistency violation: " + "; ".join(reasons),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "checked_bindings": checked_bindings,
                },
            )

        if not checked_bindings:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No tracked stateful entity fields in '{tool_name}' output",
                details={"tool_name": tool_name},
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"State consistency preserved across {len(checked_bindings)} entity binding(s)",
            details={
                "tool_name": tool_name,
                "checked_bindings": checked_bindings,
            },
        )
