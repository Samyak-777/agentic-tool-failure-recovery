"""
semantic_validation/core/pipeline.py

SemanticValidationPipeline — orchestrates all checkers (L1–L10).

Responsibilities:
    1. Instantiate enabled checkers from config.
    2. Run each checker in order (L1 → L9, L10 only if enabled).
    3. Aggregate CheckResults into a ValidationResult with PipelineStatus.
    4. Handle exceptions per fail_mode (open/closed).
    5. Provide latency measurement per checker and total.

Integration point:
    Called by ExecutionEngine._intercept_tool_call() AFTER the tool result
    is produced (perturbation OR real execution), BEFORE agent.receive_tool_result().

What the pipeline knows (legitimate):
    - tool_name, arguments, result (the three parameters of a tool call)
    - output schema from YAML (tool contract)
    - prior validated state (own observation history)
    - context.history (InferenceContext — prior tool calls)

What the pipeline does NOT know (enforced by not passing these):
    - perturbation mode (P1/P2/P3/P4)
    - ground truth expected result
    - oracle paths
    - evaluator verdicts
"""

from __future__ import annotations

import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..checkers.base import BaseChecker
from ..config.validation_config import ValidationConfig
from ..core.result import CheckResult, ValidationResult, build_summary_reason
from ..core.state_store import (
    ExecutionValidationState,
    ValidationStateStore,
    GLOBAL_STATE_STORE,
)
from ..core.status import CheckerStatus, PipelineStatus
from ..schema.extractor import SchemaExtractor
from ..schema.range_registry import RangeRegistry


class SemanticValidationPipeline:
    """
    Orchestrates the full semantic validation pipeline for one tool call.

    Create one pipeline per ExecutionEngine (not per tool call).
    The pipeline is stateless per call — mutable state lives in
    ExecutionValidationState (keyed by execution_id).

    Args:
        config:       Validated ValidationConfig.
        tool_loader:  ToolLoader instance from ExecutionEngine.
        state_store:  ValidationStateStore (defaults to GLOBAL_STATE_STORE).
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        config: ValidationConfig,
        tool_loader: Any,
        state_store: Optional[ValidationStateStore] = None,
    ) -> None:
        self.config = config
        self.tool_loader = tool_loader
        self.state_store = state_store or GLOBAL_STATE_STORE

        # Build shared infrastructure passed to checkers
        self.schema_extractor = SchemaExtractor(tool_loader)
        self.range_registry = RangeRegistry()

        # Lazily-built checker list (built once per pipeline instance)
        self._checkers: Optional[List[BaseChecker]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        execution_id: str,
        task_id: str,
        step: int,
        context: Optional[Any] = None,
    ) -> ValidationResult:
        """
        Run the full validation pipeline for one tool call.

        Args:
            tool_name:    Name of the tool whose output is being validated.
            arguments:    Arguments the agent passed.
            result:       Raw tool output dict.
            execution_id: UUID for this task execution (isolation key).
            task_id:      ToolMaze task_id (for reporting).
            step:         Step number within the execution.
            context:      InferenceContext (for L8/L9 cross-call access).

        Returns:
            ValidationResult with aggregate PipelineStatus and per-checker results.
        """
        pipeline_start = time.perf_counter()

        # Retrieve per-execution state (created by ExecutionEngine at task start)
        state = self.state_store.get_state(execution_id)

        # Build ValidationResult shell
        val_result = ValidationResult(
            pipeline_status=PipelineStatus.INCONCLUSIVE,  # updated at end
            tool_name=tool_name,
            execution_id=execution_id,
            task_id=task_id,
            step=step,
            validator_version=self.VERSION,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Run each enabled checker
        for checker in self._get_checkers():
            check_result = self._run_checker_safely(
                checker=checker,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                state=state,
                context=context,
            )
            val_result.add_check(check_result)

        # Aggregate pipeline status
        checker_statuses = [cr.status for cr in val_result.checks.values()]
        val_result.pipeline_status = PipelineStatus.aggregate(checker_statuses)

        # Build human-readable reason
        val_result.reason = build_summary_reason(
            val_result.checks,
            val_result.failed_checks,
            val_result.pipeline_status,
        )

        # Record total latency
        val_result.total_latency_ms = (
            (time.perf_counter() - pipeline_start) * 1000
        )

        return val_result

    # ------------------------------------------------------------------
    # Lifecycle helpers (called by ExecutionEngine)
    # ------------------------------------------------------------------

    def create_execution_state(
        self, execution_id: str, task_id: str
    ) -> ExecutionValidationState:
        """
        Create isolated state for a new task execution.

        Called by ExecutionEngine.__init__() before engine.run().

        Args:
            execution_id: UUID. Must be unique per task execution.
            task_id:      ToolMaze task_id for reporting.

        Returns:
            Newly created ExecutionValidationState.
        """
        return self.state_store.create_state(execution_id, task_id)

    def destroy_execution_state(self, execution_id: str) -> None:
        """
        Clean up state after a task execution completes.

        Called by ExecutionEngine after engine.run() returns.

        Args:
            execution_id: UUID to clean up.
        """
        self.state_store.destroy_state(execution_id)

    # ------------------------------------------------------------------
    # Checker construction (lazy, once per pipeline instance)
    # ------------------------------------------------------------------

    def _get_checkers(self) -> List[BaseChecker]:
        """Build (once) and return the ordered list of enabled checkers."""
        if self._checkers is None:
            self._checkers = self._build_checkers()
        return self._checkers

    def _build_checkers(self) -> List[BaseChecker]:
        """
        Instantiate enabled checkers in canonical order L1 → L10.

        Checkers not enabled in config.checkers are completely omitted
        (not even instantiated). This supports clean ablation studies.
        """
        checkers: List[BaseChecker] = []
        flags = self.config.checkers

        # L1 — Schema Verification
        if flags.schema:
            from ..checkers.schema_checker import SchemaChecker
            checkers.append(SchemaChecker(self.schema_extractor))

        # L2 — Data Type Enforcement
        if flags.type:
            from ..checkers.type_checker import TypeChecker
            checkers.append(TypeChecker(self.schema_extractor))

        # L3 — Required Field Checks
        if flags.required:
            from ..checkers.required_checker import RequiredFieldChecker
            checkers.append(RequiredFieldChecker(self.schema_extractor))

        # L4 — Value Range Validation
        if flags.range:
            from ..checkers.range_checker import RangeChecker
            checkers.append(RangeChecker(self.range_registry))

        # L5 — Temporal Consistency
        if flags.temporal:
            from ..checkers.temporal_checker import TemporalChecker
            checkers.append(TemporalChecker(self.config.temporal))

        # L6 — Entity Consistency
        if flags.entity:
            from ..checkers.entity_checker import EntityChecker
            checkers.append(EntityChecker(self.schema_extractor))

        # L7 — Cross-Field Rules
        if flags.cross_field:
            from ..checkers.cross_field_checker import CrossFieldChecker
            checkers.append(CrossFieldChecker())

        # L8 — Accumulated State Consistency
        if flags.state:
            from ..checkers.state_checker import StateChecker
            checkers.append(StateChecker())

        # L9 — Cross-Tool Consistency
        if flags.cross_tool:
            from ..checkers.cross_tool_checker import CrossToolChecker
            checkers.append(CrossToolChecker())

        # L10 — Independent LLM Verification (disabled throughout initial phases)
        if flags.llm:
            from ..checkers.llm_checker import LLMChecker
            checkers.append(LLMChecker(self.config.llm))

        return checkers

    # ------------------------------------------------------------------
    # Safe checker execution
    # ------------------------------------------------------------------

    def _run_checker_safely(
        self,
        checker: BaseChecker,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        state: Optional[ExecutionValidationState],
        context: Optional[Any],
    ) -> CheckResult:
        """
        Run a checker and catch any unexpected exceptions.

        Behaviour on exception:
            fail_open  (default): return CheckerStatus.ERROR, treated as NOT_APPLICABLE
            fail_closed:          return CheckerStatus.ERROR, treated as INVALID by aggregate

        Note: We always return CheckerStatus.ERROR on exception (not INVALID directly).
        The PipelineStatus.aggregate() logic treats ERROR without INVALID as
        pipeline ERROR (not INVALID). Only if fail_closed, the pipeline will report
        ERROR which the sandbox can choose to treat as INVALID at the injection layer.

        This preserves the distinction between "we detected a violation" (INVALID)
        and "we crashed while trying to validate" (ERROR).

        Args:
            checker:    The checker to run.
            tool_name:  Tool name for the check call.
            arguments:  Tool arguments.
            result:     Tool output.
            state:      Per-execution validation state.
            context:    InferenceContext.

        Returns:
            CheckResult (guaranteed, never raises).
        """
        start = time.perf_counter()
        try:
            check_result = checker.check(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                state=state,
                context=context,
            )
            check_result.latency_ms = (time.perf_counter() - start) * 1000
            return check_result

        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            error_detail = traceback.format_exc()
            return CheckResult(
                checker_name=checker.name,
                status=CheckerStatus.ERROR,
                reason=(
                    f"Checker '{checker.name}' raised an unexpected exception: "
                    f"{type(exc).__name__}: {exc}"
                ),
                details={
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "traceback": error_detail,
                    "fail_mode": self.config.fail_mode,
                },
                latency_ms=latency_ms,
            )
