"""
semantic_validation/checkers/base.py

Abstract base class for all SVL checkers (L1–L10).

Every concrete checker must implement `check()`. The pipeline calls
this method and handles exceptions according to fail_mode.

Design contract:
    - Checkers must ONLY use information legitimately available at validation time:
        * tool_name (string)
        * arguments (what the agent passed)
        * result (raw output dict from plugin/perturbation)
        * output_schema (from tool definition YAML — exists at validation time)
        * state (ExecutionValidationState — previously validated observations)
        * context.history (prior tool call records in InferenceContext)
    - Checkers must NEVER access:
        * perturbation labels (P1/P2/P3/P4)
        * ground truth expected results
        * oracle recovery paths
        * evaluator verdicts
        * task_json internals beyond what is passed explicitly
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.result import CheckResult
from ..core.state_store import ExecutionValidationState


class BaseChecker(ABC):
    """
    Abstract base for all SVL checkers.

    Subclasses implement `check()` and return a CheckResult.
    They should NEVER raise exceptions from `check()` — use
    CheckerStatus.ERROR with a reason string for internal failures.
    """

    #: Unique name for this checker. Used as key in ValidationResult.checks.
    name: str = "base"

    @abstractmethod
    def check(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        state: Optional[ExecutionValidationState] = None,
        context: Optional[Any] = None,
    ) -> CheckResult:
        """
        Execute the check and return a CheckResult.

        Args:
            tool_name:  Name of the tool whose output is being validated.
            arguments:  Arguments the agent passed to the tool call.
            result:     Raw output dict from the tool plugin or perturbation.
            state:      Mutable per-execution validation state (L8 only).
            context:    InferenceContext for accessing prior tool call history
                        (L8, L9 only). Passed as Any to avoid circular imports.

        Returns:
            CheckResult with status, reason, and details.

        Note:
            Implementations must catch all exceptions internally and return
            CheckResult(status=CheckerStatus.ERROR, ...) rather than letting
            exceptions propagate. The pipeline provides an outer safety net,
            but checkers are responsible for clean error handling.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
