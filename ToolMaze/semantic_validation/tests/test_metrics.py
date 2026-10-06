"""Unit tests for validation metrics calculator."""

import pytest
from semantic_validation.metrics import ValidationMetricsCalculator, compute_validation_metrics


def test_metrics_calculation():
    calc = ValidationMetricsCalculator()

    # Step 1: Perturbed tool, detected as INVALID (TP)
    calc.record_step(is_perturbed=True, pipeline_status="INVALID", total_latency_ms=1.5, failed_checks=["type"])

    # Step 2: Perturbed tool, missed (FN)
    calc.record_step(is_perturbed=True, pipeline_status="VALID", total_latency_ms=1.2)

    # Step 3: Clean tool, passed as VALID (TN)
    calc.record_step(is_perturbed=False, pipeline_status="VALID", total_latency_ms=0.8)

    # Step 4: Clean tool, falsely flagged as INVALID (FP)
    calc.record_step(is_perturbed=False, pipeline_status="INVALID", total_latency_ms=1.0, failed_checks=["range"])

    summary = calc.get_summary()

    # VDR = TP / (TP + FN) = 1 / (1 + 1) = 0.5
    assert summary["vdr"] == 0.5

    # VP = TP / (TP + FP) = 1 / (1 + 1) = 0.5
    assert summary["vp"] == 0.5

    # FPR = FP / (FP + TN) = 1 / (1 + 1) = 0.5
    assert summary["fpr"] == 0.5

    # Total calls = 4
    assert summary["total_calls"] == 4
    assert summary["clean_calls"] == 2
    assert summary["perturbed_calls"] == 2
    assert summary["checker_detections"]["type"] == 1
    assert summary["checker_detections"]["range"] == 1
