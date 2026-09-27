"""
semantic_validation/core/result.py

Defines the canonical result dataclasses for the SVL.

Two levels:
    CheckResult     — result of one individual checker
    ValidationResult — aggregated result across all checkers for one tool call

Research note:
    When pipeline status is INVALID, the sandbox injects:
        {
            "validation_failed": true,
            "validation_status": "INVALID",
            "validation_reason": "...",
            "validation_failed_checks": [...],
            "untrusted_output": <original result dict>
        }
    The agent sees this and can choose to retry, switch tools, or stop.
    The SVL does NOT choose the recovery strategy.

    When pipeline status is INCONCLUSIVE or VALID, the original result
    is passed to the agent unchanged.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

from .status import CheckerStatus, PipelineStatus


@dataclass
class CheckResult:
    """
    Result produced by a single checker for one tool call.

    Attributes:
        checker_name:   Identifier of the checker (e.g., "schema", "range").
        status:         VALID | INVALID | NOT_APPLICABLE | ERROR.
        reason:         Human-readable explanation (required when INVALID).
        details:        Structured evidence dict (e.g., field name, actual value,
                        expected value, rule_id, source).
        latency_ms:     Wall-clock time taken by this checker in milliseconds.
    """
    checker_name: str
    status: CheckerStatus
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checker_name": self.checker_name,
            "status": self.status.value,
            "reason": self.reason,
            "details": self.details,
            "latency_ms": round(self.latency_ms, 3),
        }


@dataclass
class ValidationResult:
    """
    Aggregated validation result for one tool call.

    Attributes:
        pipeline_status:    Overall VALID | INVALID | INCONCLUSIVE | ERROR.
        tool_name:          Name of the tool that produced the output.
        execution_id:       UUID for this benchmark run (unique per task execution).
        task_id:            ToolMaze task identifier (for reporting).
        step:               Tool call step number within the task.
        checks:             Dict mapping checker_name → CheckResult.
        failed_checks:      Names of checkers that returned INVALID.
        warnings:           Non-blocking issues flagged by checkers.
        reason:             Human-readable summary of the overall decision.
        validator_version:  SVL version string.
        total_latency_ms:   Total wall-clock time across all checkers.
        timestamp:          ISO 8601 timestamp of validation completion.
    """
    pipeline_status: PipelineStatus
    tool_name: str
    execution_id: str
    task_id: str
    step: int
    checks: Dict[str, CheckResult] = field(default_factory=dict)
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    reason: str = ""
    validator_version: str = "1.0.0"
    total_latency_ms: float = 0.0
    timestamp: str = ""

    def add_check(self, result: CheckResult) -> None:
        """Register a checker result and update failed_checks accordingly."""
        self.checks[result.checker_name] = result
        if result.status == CheckerStatus.INVALID:
            self.failed_checks.append(result.checker_name)

    def add_warning(self, warning: str) -> None:
        """Add a non-blocking warning."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_status": self.pipeline_status.value,
            "tool_name": self.tool_name,
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "step": self.step,
            "checks": {name: cr.to_dict() for name, cr in self.checks.items()},
            "failed_checks": self.failed_checks,
            "warnings": self.warnings,
            "reason": self.reason,
            "validator_version": self.validator_version,
            "total_latency_ms": round(self.total_latency_ms, 3),
            "timestamp": self.timestamp,
        }

    def to_agent_failure_payload(
        self, original_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the structured payload injected into the tool result when INVALID.

        The original corrupted output is included under 'untrusted_output'
        so the agent has raw data for reasoning, but the explicit 'untrusted_output'
        key signals it MUST NOT be acted on without verification.

        This is never called for VALID / INCONCLUSIVE results.

        Args:
            original_result: The raw tool output dict before injection.

        Returns:
            Dict the agent receives instead of the raw result.
        """
        assert self.pipeline_status == PipelineStatus.INVALID, (
            "to_agent_failure_payload must only be called for INVALID results"
        )
        return {
            "validation_failed": True,
            "validation_status": "INVALID",
            "validation_reason": self.reason,
            "validation_failed_checks": self.failed_checks,
            "untrusted_output": original_result,
        }


def build_summary_reason(
    checks: Dict[str, CheckResult],
    failed_checks: List[str],
    pipeline_status: PipelineStatus,
) -> str:
    """
    Build a concise human-readable summary reason for the ValidationResult.

    Args:
        checks:          All checker results.
        failed_checks:   Names of INVALID checkers.
        pipeline_status: Overall pipeline status.

    Returns:
        A single-sentence summary string.
    """
    if pipeline_status == PipelineStatus.VALID:
        n_valid = sum(
            1 for r in checks.values() if r.status == CheckerStatus.VALID
        )
        return f"{n_valid} checker(s) confirmed output as valid."

    if pipeline_status == PipelineStatus.INCONCLUSIVE:
        return (
            "No applicable validation checks could be executed for this "
            "tool/output combination. Validity is inconclusive."
        )

    if pipeline_status == PipelineStatus.INVALID:
        reasons = []
        for name in failed_checks:
            r = checks.get(name)
            if r and r.reason:
                reasons.append(f"[{name}] {r.reason}")
        return "Validation failed: " + "; ".join(reasons) if reasons else "Validation failed."

    if pipeline_status == PipelineStatus.ERROR:
        return "Validation pipeline encountered an internal error."

    return "Unknown validation state."
