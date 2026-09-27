"""
Semantic Validation Layer (SVL) for ToolMaze.

Entry point for the validation pipeline. Import SemanticValidationPipeline
to embed validation into the execution engine.

Architecture:
    core/       — result dataclasses, status enum, pipeline, state store
    checkers/   — individual validation checkers (L1–L10)
    schema/     — schema extraction + range registry
    rules/      — cross-field and cross-tool rule definitions
    config/     — ValidationConfig dataclass
    metrics/    — VDR, VP, FPR, RAD, VO, VC calculators
    tests/      — unit + integration tests

Research note:
    The SVL is inserted AFTER tool execution and perturbation injection,
    BEFORE the agent receives the result. It does NOT have access to:
      - P1/P2/P3/P4 perturbation labels
      - ground-truth expected results
      - oracle recovery paths
      - evaluator verdicts
    All assumptions are documented in assumptions.md.
"""

from .config import ValidationConfig, CheckerFlags, TemporalConfig, LLMVerifierConfig
from .core import (
    CheckResult,
    ValidationResult,
    CheckerStatus,
    PipelineStatus,
    SemanticValidationPipeline,
    ExecutionValidationState,
    ValidationStateStore,
    GLOBAL_STATE_STORE,
)

__version__ = "1.0.0"

__all__ = [
    "ValidationConfig",
    "CheckerFlags",
    "TemporalConfig",
    "LLMVerifierConfig",
    "CheckResult",
    "ValidationResult",
    "CheckerStatus",
    "PipelineStatus",
    "SemanticValidationPipeline",
    "ExecutionValidationState",
    "ValidationStateStore",
    "GLOBAL_STATE_STORE",
]
