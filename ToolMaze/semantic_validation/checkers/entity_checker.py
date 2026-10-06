"""
semantic_validation/checkers/entity_checker.py

Checker 6 (L6): Entity Consistency Checker.

Verifies that the entity returned in a tool's output corresponds to the
entity requested in the agent's tool call arguments.

Detects implicit perturbations (P3/P4) where a tool returns valid data for the
wrong entity (e.g., requested "Tokyo", returned weather for "Osaka").

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If neither arguments nor output contain comparable entity fields: NOT_APPLICABLE.
    - If requested entity field is present in output and differs: INVALID.
    - If matching entity field matches: VALID.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..schema.extractor import SchemaExtractor
from .base import BaseChecker


# Common entity field mappings: (argument_key, result_key)
CANDIDATE_ENTITY_PAIRS: List[Tuple[str, str]] = [
    ("city", "city"),
    ("ticker", "ticker"),
    ("ticker", "symbol"),
    ("symbol", "symbol"),
    ("symbol", "ticker"),
    ("name", "name"),
    ("user_id", "user_id"),
    ("email", "email"),
    ("hotel_id", "hotel_id"),
    ("flight_number", "flight_number"),
    ("meeting_id", "meeting_id"),
    ("contact_name", "name"),
]


class EntityChecker(BaseChecker):
    """L6: Checks entity fidelity between input arguments and output response."""

    name: str = "entity"

    def __init__(self, schema_extractor: Optional[SchemaExtractor] = None) -> None:
        self.schema_extractor = schema_extractor

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
                reason="Tool returned an explicit error response; entity checking does not apply",
                details={"error": str(result.get("error"))},
            )

        compared_pairs: List[Dict[str, Any]] = []
        violations: List[Dict[str, Any]] = []

        # Find matching entity keys between arguments and result
        for arg_key, res_key in CANDIDATE_ENTITY_PAIRS:
            if arg_key in arguments and res_key in result:
                req_val = arguments[arg_key]
                res_val = result[res_key]

                if req_val is None or res_val is None:
                    continue

                req_str = str(req_val).strip().lower()
                res_str = str(res_val).strip().lower()

                match = (req_str == res_str)
                compared_pairs.append({
                    "arg_key": arg_key,
                    "res_key": res_key,
                    "requested": req_val,
                    "returned": res_val,
                    "match": match,
                })

                if not match:
                    violations.append({
                        "field": res_key,
                        "requested": req_val,
                        "returned": res_val,
                        "reason": f"Requested {arg_key}='{req_val}', but output returned {res_key}='{res_val}'",
                    })

        if not compared_pairs:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No matching entity fields between arguments and output for tool '{tool_name}'",
                details={"arguments": list(arguments.keys()), "output": list(result.keys())},
            )

        if violations:
            violation_msgs = [v["reason"] for v in violations]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="Entity mismatch detected: " + "; ".join(violation_msgs),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "compared_pairs": compared_pairs,
                },
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"Entity consistency confirmed ({len(compared_pairs)} entity field(s) matched)",
            details={
                "tool_name": tool_name,
                "compared_pairs": compared_pairs,
            },
        )
