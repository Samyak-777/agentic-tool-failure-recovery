"""
semantic_validation/checkers/required_checker.py

Checker 3 (L3): Required Field Checks.

Ensures all fields specified in the tool's output schema contract are
both present and non-null in the output.

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE (error path).
    - If tool has no output_schema: NOT_APPLICABLE.
    - If any declared schema field is missing or None: INVALID.
    - Otherwise: VALID.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from ..schema.extractor import SchemaExtractor
from .base import BaseChecker


class RequiredFieldChecker(BaseChecker):
    """L3: Checks that all schema-mandated fields are present and non-null."""

    name: str = "required"

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
                reason="Tool returned an explicit error response; required fields do not apply",
                details={"error": str(result.get("error"))},
            )

        schema = self.schema_extractor.get_output_schema(tool_name)
        if schema is None:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No output_schema defined for tool '{tool_name}'",
                details={"tool_name": tool_name},
            )

        missing_fields: List[str] = []
        null_fields: List[str] = []

        for field_name in schema.keys():
            if field_name not in result:
                missing_fields.append(field_name)
            elif result[field_name] is None:
                null_fields.append(field_name)

        if missing_fields or null_fields:
            issues = []
            if missing_fields:
                issues.append(f"missing: {missing_fields}")
            if null_fields:
                issues.append(f"null: {null_fields}")

            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason=f"Required field violation for '{tool_name}': {'; '.join(issues)}",
                details={
                    "tool_name": tool_name,
                    "missing_fields": missing_fields,
                    "null_fields": null_fields,
                    "expected_fields": list(schema.keys()),
                },
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"All {len(schema)} required fields present and non-null",
            details={
                "tool_name": tool_name,
                "verified_fields": list(schema.keys()),
            },
        )
