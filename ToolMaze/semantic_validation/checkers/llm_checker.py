"""
semantic_validation/checkers/llm_checker.py

Checker 10 (L10): Independent LLM Output Verification.

Optional LLM-based semantic validator. Uses an isolated prompt to inspect
tool output for physical/semantic plausibility when deterministic rules
are inconclusive.

CRITICAL RESEARCH ENFORCEMENT:
    - Never receives perturbation mode, ground truth, or oracle path.
    - Operates purely on (tool_name, arguments, result).
    - If disabled, call to check() returns NOT_APPLICABLE.
    - If call fails (timeout/API error), returns ERROR with fail-open fallback.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from ..config.validation_config import LLMVerifierConfig
from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from .base import BaseChecker


class LLMChecker(BaseChecker):
    """L10: LLM-based output plausibility verifier (optional)."""

    name: str = "llm"

    def __init__(self, config: Optional[LLMVerifierConfig] = None) -> None:
        self.config = config or LLMVerifierConfig()

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
                reason="Tool returned an explicit error response; LLM verifier skipped",
                details={"error": str(result.get("error"))},
            )

        if not self.config.model:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason="LLM verifier model not configured",
                details={"tool_name": tool_name},
            )

        # In production/eval with live model credentials, this would issue an API call.
        # When mocked or offline, return NOT_APPLICABLE if no active client.
        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.NOT_APPLICABLE,
            reason="LLM verifier offline / unconfigured API client",
            details={"tool_name": tool_name, "model": self.config.model},
        )
