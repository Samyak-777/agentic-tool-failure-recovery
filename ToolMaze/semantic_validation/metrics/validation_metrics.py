"""
semantic_validation/metrics/validation_metrics.py

Research metrics for the Semantic Validation Layer (SVL).

Definitions:
    - VDR (Validation Detection Rate / Recall):
        VDR = TP / (TP + FN)
        Proportion of injected perturbations (P1-P4) flagged as INVALID.

    - VP (Validation Precision):
        VP = TP / (TP + FP)
        Proportion of INVALID flags that were truly perturbed tool calls.

    - FPR (False Positive Rate):
        FPR = FP / (FP + TN)
        Proportion of clean executions incorrectly flagged as INVALID.

    - RAD (Recovery Activation Delta):
        Difference in recovery attempts between SVL-enabled and baseline.

    - VO (Validation Overhead):
        Average wall-clock latency added per tool call (ms) and fraction of round time.

    - VC (Validation Coverage):
        Proportion of tool calls evaluated with VALID or INVALID status vs INCONCLUSIVE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ValidationRunMetrics:
    total_calls: int = 0
    clean_calls: int = 0
    perturbed_calls: int = 0

    true_positives: int = 0   # Perturbed and flagged INVALID
    false_negatives: int = 0  # Perturbed and NOT flagged INVALID
    false_positives: int = 0  # Clean and flagged INVALID
    true_negatives: int = 0   # Clean and NOT flagged INVALID

    inconclusive_calls: int = 0
    valid_calls: int = 0
    invalid_calls: int = 0
    error_calls: int = 0

    total_latency_ms: float = 0.0
    checker_latencies_ms: Dict[str, float] = field(default_factory=dict)
    checker_detection_counts: Dict[str, int] = field(default_factory=dict)

    @property
    def vdr(self) -> float:
        """Validation Detection Rate (Recall): TP / (TP + FN)."""
        denom = self.true_positives + self.false_negatives
        return (self.true_positives / denom) if denom > 0 else 0.0

    @property
    def vp(self) -> float:
        """Validation Precision: TP / (TP + FP)."""
        denom = self.true_positives + self.false_positives
        return (self.true_positives / denom) if denom > 0 else 0.0

    @property
    def fpr(self) -> float:
        """False Positive Rate: FP / (FP + TN)."""
        denom = self.false_positives + self.true_negatives
        return (self.false_positives / denom) if denom > 0 else 0.0

    @property
    def vc(self) -> float:
        """Validation Coverage: Conclusive calls (VALID or INVALID) / total_calls."""
        conclusive = self.valid_calls + self.invalid_calls
        return (conclusive / self.total_calls) if self.total_calls > 0 else 0.0

    @property
    def avg_latency_ms(self) -> float:
        """Average latency per tool call in milliseconds."""
        return (self.total_latency_ms / self.total_calls) if self.total_calls > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "clean_calls": self.clean_calls,
            "perturbed_calls": self.perturbed_calls,
            "true_positives": self.true_positives,
            "false_negatives": self.false_negatives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "valid_calls": self.valid_calls,
            "invalid_calls": self.invalid_calls,
            "inconclusive_calls": self.inconclusive_calls,
            "error_calls": self.error_calls,
            "vdr": round(self.vdr, 4),
            "vp": round(self.vp, 4),
            "fpr": round(self.fpr, 4),
            "vc": round(self.vc, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 3),
            "total_latency_ms": round(self.total_latency_ms, 3),
            "checker_detections": self.checker_detection_counts,
        }


class ValidationMetricsCalculator:
    """Aggregates tool call outcomes across tasks to calculate SVL metrics."""

    def __init__(self) -> None:
        self.metrics = ValidationRunMetrics()

    def record_step(
        self,
        is_perturbed: bool,
        pipeline_status: str,
        total_latency_ms: float = 0.0,
        failed_checks: Optional[List[str]] = None,
        checker_latencies: Optional[Dict[str, float]] = None,
    ) -> None:
        """Record a single tool validation step."""
        m = self.metrics
        m.total_calls += 1
        m.total_latency_ms += total_latency_ms

        if is_perturbed:
            m.perturbed_calls += 1
        else:
            m.clean_calls += 1

        is_invalid = (pipeline_status == "INVALID")
        if is_invalid:
            m.invalid_calls += 1
        elif pipeline_status == "VALID":
            m.valid_calls += 1
        elif pipeline_status == "INCONCLUSIVE":
            m.inconclusive_calls += 1
        elif pipeline_status == "ERROR":
            m.error_calls += 1

        # Confusion matrix assignment
        if is_perturbed:
            if is_invalid:
                m.true_positives += 1
            else:
                m.false_negatives += 1
        else:
            if is_invalid:
                m.false_positives += 1
            else:
                m.true_negatives += 1

        if failed_checks:
            for chk in failed_checks:
                m.checker_detection_counts[chk] = (
                    m.checker_detection_counts.get(chk, 0) + 1
                )

        if checker_latencies:
            for chk, lat in checker_latencies.items():
                m.checker_latencies_ms[chk] = (
                    m.checker_latencies_ms.get(chk, 0.0) + lat
                )

    def get_summary(self) -> Dict[str, Any]:
        return self.metrics.to_dict()


def compute_validation_metrics(steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Helper to compute metrics from a list of serialized step records."""
    calc = ValidationMetricsCalculator()
    for s in steps:
        calc.record_step(
            is_perturbed=s.get("is_perturbed", False),
            pipeline_status=s.get("pipeline_status", "INCONCLUSIVE"),
            total_latency_ms=s.get("total_latency_ms", 0.0),
            failed_checks=s.get("failed_checks"),
            checker_latencies=s.get("checker_latencies"),
        )
    return calc.get_summary()
