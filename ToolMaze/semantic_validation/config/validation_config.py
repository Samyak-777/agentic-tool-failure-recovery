"""
semantic_validation/config/validation_config.py

Configuration dataclass for the Semantic Validation Layer.

Loaded from the 'validation:' block in eval_config.yaml.
Provides the canonical SEMANTIC_VALIDATION_ENABLED switch.

When enabled=False the SVL is completely bypassed — baseline
behaviour is IDENTICAL to running without the SVL code present.

Research note (from approved plan):
    - L10 (LLM verifier) is disabled throughout pilot and first
      full evaluation. It remains behind the 'llm' flag for later
      ablation studies only.
    - 'fail_mode' defaults to "open": a validator exception is
      treated as NOT_APPLICABLE, not INVALID. This prevents the
      SVL from becoming a single point of failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class TemporalConfig:
    """
    Configuration for the Temporal Consistency checker (L5).

    Attributes:
        max_timestamp_age_seconds:
            If set, timestamps older than this many seconds relative to
            the run's start time are flagged as STALE_TIMESTAMP.
            None (default) = staleness check disabled.
            This is an EXPLICIT_PROJECT_RULE assumption — documented in
            assumptions.md. Do not set without justification.
        future_timestamp_warning:
            If True, timestamps more than 1 day in the future produce a
            WARNING (non-blocking). Default True.
    """
    max_timestamp_age_seconds: Optional[float] = None
    future_timestamp_warning: bool = True


@dataclass
class LLMVerifierConfig:
    """
    Configuration for the optional LLM Verifier (L10).

    Disabled by default throughout the initial experiment phases.
    Only enabled as an explicit ablation after L1–L9 results are
    established.

    Attributes:
        model:            LLM model name to use. If None, inherited from
                          the judge config at runtime.
        max_tokens:       Max tokens for the verifier response.
        timeout_seconds:  Hard timeout; on timeout the checker returns ERROR
                          (treated as NOT_APPLICABLE in FAIL_OPEN mode).
        temperature:      Sampling temperature (kept low for stability).
    """
    model: Optional[str] = None
    max_tokens: int = 256
    timeout_seconds: float = 10.0
    temperature: float = 0.0


@dataclass
class CheckerFlags:
    """
    Per-checker enable/disable flags for ablation support.

    Each flag maps to one checker in the pipeline.
    Setting a flag to False completely skips that checker —
    the CheckResult is omitted from ValidationResult.checks.

    Research note:
        This enables independent ablation per checker:
        e.g. schema=False to measure the marginal value of schema checking.
    """
    schema: bool = True        # L1
    type: bool = True          # L2
    required: bool = True      # L3
    range: bool = True         # L4
    temporal: bool = True      # L5
    entity: bool = True        # L6
    cross_field: bool = True   # L7
    state: bool = True         # L8
    cross_tool: bool = True    # L9
    llm: bool = False          # L10 — DISABLED, see research note above


@dataclass
class ValidationConfig:
    """
    Root configuration for the Semantic Validation Layer.

    Attributes:
        enabled:     Master switch. False = bypass SVL entirely.
                     Corresponds to SEMANTIC_VALIDATION_ENABLED=false.
        fail_mode:   "open"  — exceptions in validators → NOT_APPLICABLE.
                     "closed" — exceptions in validators → INVALID.
                     Default: "open" (prevents SVL from blocking the agent).
        checkers:    Per-checker enable/disable flags for ablation.
        temporal:    Temporal checker sub-configuration.
        llm:         LLM verifier sub-configuration (L10, disabled by default).
    """
    enabled: bool = False
    fail_mode: str = "open"        # "open" | "closed"
    checkers: CheckerFlags = field(default_factory=CheckerFlags)
    temporal: TemporalConfig = field(default_factory=TemporalConfig)
    llm: LLMVerifierConfig = field(default_factory=LLMVerifierConfig)

    @property
    def fail_open(self) -> bool:
        """True if validator exceptions should be treated as NOT_APPLICABLE."""
        return self.fail_mode.lower() == "open"

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "ValidationConfig":
        """
        Parse from the raw 'validation:' dict loaded from YAML.

        Expected YAML shape:
            validation:
              enabled: true
              fail_mode: "open"
              checkers:
                schema: true
                type: true
                required: true
                range: true
                temporal: true
                entity: true
                cross_field: true
                state: true
                cross_tool: true
                llm: false
              temporal:
                max_timestamp_age_seconds: null
                future_timestamp_warning: true
              llm:
                model: null
                max_tokens: 256
                timeout_seconds: 10.0
                temperature: 0.0

        Args:
            raw: Dict from yaml.safe_load.

        Returns:
            ValidationConfig instance.
        """
        if not raw:
            return cls()

        checker_raw = raw.get("checkers", {})
        checkers = CheckerFlags(
            schema=checker_raw.get("schema", True),
            type=checker_raw.get("type", True),
            required=checker_raw.get("required", True),
            range=checker_raw.get("range", True),
            temporal=checker_raw.get("temporal", True),
            entity=checker_raw.get("entity", True),
            cross_field=checker_raw.get("cross_field", True),
            state=checker_raw.get("state", True),
            cross_tool=checker_raw.get("cross_tool", True),
            llm=checker_raw.get("llm", False),  # Always default False
        )

        temporal_raw = raw.get("temporal", {})
        temporal = TemporalConfig(
            max_timestamp_age_seconds=temporal_raw.get("max_timestamp_age_seconds"),
            future_timestamp_warning=temporal_raw.get("future_timestamp_warning", True),
        )

        llm_raw = raw.get("llm", {})
        llm = LLMVerifierConfig(
            model=llm_raw.get("model"),
            max_tokens=llm_raw.get("max_tokens", 256),
            timeout_seconds=llm_raw.get("timeout_seconds", 10.0),
            temperature=llm_raw.get("temperature", 0.0),
        )

        return cls(
            enabled=raw.get("enabled", False),
            fail_mode=raw.get("fail_mode", "open"),
            checkers=checkers,
            temporal=temporal,
            llm=llm,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config for logging in experiment metadata."""
        return {
            "enabled": self.enabled,
            "fail_mode": self.fail_mode,
            "checkers": {
                "schema": self.checkers.schema,
                "type": self.checkers.type,
                "required": self.checkers.required,
                "range": self.checkers.range,
                "temporal": self.checkers.temporal,
                "entity": self.checkers.entity,
                "cross_field": self.checkers.cross_field,
                "state": self.checkers.state,
                "cross_tool": self.checkers.cross_tool,
                "llm": self.checkers.llm,
            },
            "temporal": {
                "max_timestamp_age_seconds": self.temporal.max_timestamp_age_seconds,
                "future_timestamp_warning": self.temporal.future_timestamp_warning,
            },
            "llm": {
                "model": self.llm.model,
                "max_tokens": self.llm.max_tokens,
                "timeout_seconds": self.llm.timeout_seconds,
                "temperature": self.llm.temperature,
            },
        }
