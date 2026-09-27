"""
semantic_validation/checkers/schema_checker.py

Checker 1 (L1): Output Schema Verification.

Validates that the output dictionary adheres to the declared output schema
from the tool definition (MCP output_schema).

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE (explicit error path).
    - If tool has no output_schema in definitions: NOT_APPLICABLE.
    - If any field declared in output_schema is missing: INVALID.
    - If unexpected fields appear: VALID with warning in details.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..schema.extractor import SchemaExtractor
from .base import BaseChecker


class SchemaChecker(BaseChecker):
    """L1: Verifies tool output against the MCP output_schema contract."""

    name: str = "schema"

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
                reason=f"Tool output must be a dict/JSON object, got {type(result).__name__}",
                details={"actual_type": type(result).__name__, "tool_name": tool_name},
            )

        if "error" in result:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason="Tool returned an explicit error response; output schema does not apply",
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

        expected_fields = list(schema.keys())
        missing_fields = [f for f in expected_fields if f not in result]

        if missing_fields:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason=(
                    f"Tool output for '{tool_name}' is missing required schema "
                    f"field(s): {', '.join(missing_fields)}"
                ),
                details={
                    "tool_name": tool_name,
                    "missing_fields": missing_fields,
                    "expected_fields": expected_fields,
                    "actual_fields": list(result.keys()),
                },
            )

        unexpected_fields = [f for f in result.keys() if f not in expected_fields]

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"Output satisfies schema contract ({len(expected_fields)} fields verified)",
            details={
                "tool_name": tool_name,
                "verified_fields": expected_fields,
                "unexpected_fields": unexpected_fields,
            },
        )
