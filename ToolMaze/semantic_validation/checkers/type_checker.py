"""
semantic_validation/checkers/type_checker.py

Checker 2 (L2): Data Type Enforcement.

Validates that field values in tool outputs strictly conform to the types
declared in the MCP output_schema (e.g. integer, string, boolean, number, array, object).

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If tool has no output_schema: NOT_APPLICABLE.
    - If field value does not match expected type: INVALID.
    - Strict enforcement: does NOT auto-coerce (e.g., "22" for integer is INVALID).
    - Note on Python bool: bool is a subclass of int, so strict checking ensures
      True/False is not accepted as integer/number.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..schema.extractor import SchemaExtractor
from .base import BaseChecker


TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


class TypeChecker(BaseChecker):
    """L2: Strictly enforces data types of output fields against schema."""

    name: str = "type"

    def __init__(self, schema_extractor: SchemaExtractor) -> None:
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
                reason="Tool returned an explicit error response; type checking does not apply",
                details={"error": str(result.get("error"))},
            )

        schema = self.schema_extractor.get_output_schema(tool_name)
        if schema is None:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No MCP output_schema defined for tool '{tool_name}'",
                details={"tool_name": tool_name},
            )

        violations: List[Dict[str, Any]] = []
        checked_fields: List[str] = []

        for field_name, field_def in schema.items():
            if field_name not in result:
                continue

            checked_fields.append(field_name)
            val = result[field_name]
            expected_type_str = (
                field_def.get("type") if isinstance(field_def, dict) else None
            )

            if expected_type_str is None:
                continue

            is_valid, reason = self._check_single_type(val, expected_type_str, field_def)
            if not is_valid:
                violations.append({
                    "field": field_name,
                    "expected_type": expected_type_str,
                    "actual_type": type(val).__name__,
                    "actual_value": val,
                    "violation_reason": reason,
                })

        if violations:
            violation_summaries = [
                f"Field '{v['field']}' expected {v['expected_type']}, got {v['actual_type']} ({v['violation_reason']})"
                for v in violations
            ]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="Data type violation(s): " + "; ".join(violation_summaries),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "checked_fields": checked_fields,
                },
            )

        if not checked_fields:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"None of the schema fields were present in output to type-check",
                details={"tool_name": tool_name},
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"All {len(checked_fields)} checked output fields match expected types",
            details={
                "tool_name": tool_name,
                "checked_fields": checked_fields,
            },
        )

    def _check_single_type(
        self,
        value: Any,
        expected_type_str: str,
        field_def: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Check a single value against expected type string."""
        expected_type = TYPE_MAP.get(expected_type_str.lower())
        if expected_type is None:
            return True, ""  # Unknown type schema, skip

        # Strict bool separation: bool is subclass of int in Python
        if expected_type_str.lower() in ("integer", "number"):
            if isinstance(value, bool):
                return False, "boolean cannot satisfy numeric type"
            if not isinstance(value, expected_type):
                return False, f"expected {expected_type_str}, got {type(value).__name__}"
            return True, ""

        if expected_type_str.lower() == "boolean":
            if not isinstance(value, bool):
                return False, f"expected boolean, got {type(value).__name__}"
            return True, ""

        if not isinstance(value, expected_type):
            return False, f"expected {expected_type_str}, got {type(value).__name__}"

        # Array element checking if items spec is present
        if expected_type_str.lower() == "array" and isinstance(value, list):
            items_spec = field_def.get("items")
            if isinstance(items_spec, dict) and "type" in items_spec:
                item_type_str = items_spec["type"]
                for i, item in enumerate(value):
                    item_valid, item_reason = self._check_single_type(
                        item, item_type_str, items_spec
                    )
                    if not item_valid:
                        return False, f"array element [{i}] failed: {item_reason}"

        return True, ""
