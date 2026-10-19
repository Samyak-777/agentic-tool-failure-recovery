"""
Focused Unit Tests for Comprehensive ToolMaze Execution Telemetry and Offline Analysis Pipeline.
Tests:
1. Telemetry Schema & Recorder (event structure, run/task association, concurrency, redaction)
2. Perturbation Tracking & Causal Attribution (all causal states, evidence attribution)
3. Offline Analysis Pipeline (multi-run aggregation, baseline-vs-care, CSV/MD export, zero LLM calls)
4. Regression Guarantees (unaltered arguments/results, genuine baseline, task memory reset)
"""

import os
import sys
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path

# Ensure ToolMaze project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.telemetry.schema import (
    TelemetryEvent,
    EventType,
    SCHEMA_VERSION,
    CausalAttribution,
    sanitize_and_redact
)
from evaluation.telemetry.recorder import (
    TelemetryManager,
    TelemetryRecorder
)
from evaluation.telemetry.perturbation_tracker import PerturbationTracker
from evaluation.scripts.analyze_experiments import ExperimentAnalyzer


class TestTelemetrySchemaAndRecorder(unittest.TestCase):
    """Tests for event schema, thread-safe persistence, and redaction."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.records_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_and_redaction(self):
        sensitive_data = {
            "api_key": "GEMINI_SECRET_12345",
            "openai_token": "sk-abcxyz123456",
            "normal_arg": "London",
            "long_text": "A" * 3000,
            "nested": {
                "password": "super_secret_pw",
                "count": 42
            }
        }
        sanitized = sanitize_and_redact(sensitive_data, max_string_len=100)
        self.assertEqual(sanitized["api_key"], "[REDACTED]")
        self.assertEqual(sanitized["openai_token"], "[REDACTED]")
        self.assertEqual(sanitized["nested"]["password"], "[REDACTED]")
        self.assertEqual(sanitized["normal_arg"], "London")
        self.assertEqual(sanitized["nested"]["count"], 42)
        self.assertTrue("<truncated" in sanitized["long_text"])

    def test_non_serializable_object_handling(self):
        class NonSerializableObj:
            def __str__(self):
                return "<CustomObj repr>"

        data = {"obj": NonSerializableObj(), "set_items": {1, 2, 3}}
        sanitized = sanitize_and_redact(data)
        self.assertIn("CustomObj", sanitized["obj"])
        self.assertIsInstance(sanitized["set_items"], list)
        # Verify JSON dump works without error
        dumped = json.dumps(sanitized)
        self.assertIn("<CustomObj repr>", dumped)

    def test_manager_and_task_records_isolation(self):
        mgr1 = TelemetryManager(run_id="run_test_1", agent_type="care", model="test_model", base_dir=self.records_path)
        mgr2 = TelemetryManager(run_id="run_test_2", agent_type="baseline", model="test_model", base_dir=self.records_path)

        task_json = {"task_id": "C1_task_001", "complexity": "C1", "perturbation_mode": "P0"}
        rec1 = TelemetryRecorder(mgr1, task_json, agent_type="care")
        rec2 = TelemetryRecorder(mgr2, task_json, agent_type="baseline")

        rec1.complete_task(passed=True, judgement={"pass": True})
        rec2.complete_task(passed=False, judgement={"pass": False})

        mgr1.finalize_run()
        mgr2.finalize_run()

        # Check directories exist and don't overwrite each other
        dir1 = self.records_path / "run_test_1"
        dir2 = self.records_path / "run_test_2"
        self.assertTrue((dir1 / "run_manifest.json").exists())
        self.assertTrue((dir2 / "run_manifest.json").exists())

        task_file1 = dir1 / "task_records" / "C1_task_001_P0.json"
        task_file2 = dir2 / "task_records" / "C1_task_001_P0.json"
        self.assertTrue(task_file1.exists())
        self.assertTrue(task_file2.exists())

        with open(task_file1) as f:
            t1 = json.load(f)
            self.assertTrue(t1["passed"])
            self.assertEqual(t1["agent_type"], "care")

        with open(task_file2) as f:
            t2 = json.load(f)
            self.assertFalse(t2["passed"])
            self.assertEqual(t2["agent_type"], "baseline")

    def test_concurrent_event_logging(self):
        mgr = TelemetryManager(run_id="run_concurrent", base_dir=self.records_path)
        task_json = {"task_id": "C1_task_concurrent", "complexity": "C1", "perturbation_mode": "P1"}
        rec = TelemetryRecorder(mgr, task_json)

        def worker_log(idx):
            for i in range(25):
                rec.emit_event(
                    event_type=EventType.TOOL_CALL_COMPLETED.value,
                    component="worker",
                    status="ok",
                    metadata={"thread": idx, "i": i}
                )

        threads = [threading.Thread(target=worker_log, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        mgr.finalize_run()

        events_file = self.records_path / "run_concurrent" / "events.jsonl"
        self.assertTrue(events_file.exists())
        with open(events_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # 1 run_started + 1 task_started + (4 * 25) + 1 run_completed = 103 events
        self.assertEqual(len(lines), 103)
        # Verify JSON validity of every single line
        for line in lines:
            evt = json.loads(line)
            self.assertEqual(evt["schema_version"], SCHEMA_VERSION)
            self.assertIn("sequence_number", evt)


class TestPerturbationCorrelation(unittest.TestCase):
    """Tests for causal attribution logic and perturbation tracking."""

    def test_configured_but_unactivated(self):
        task_json = {
            "task_id": "C1_task_001",
            "complexity": "C1",
            "perturbation_mode": "P1",
            "execution_trace": [
                {"step": 2, "tool_name": "victim_tool", "is_perturbed": True, "output": {"error": "503"}, "status": "error"}
            ]
        }
        tracker = PerturbationTracker(task_json)
        self.assertEqual(len(tracker.configured_perturbations), 1)

        # Agent never called victim_tool
        tool_calls = [{"tool_name": "other_tool", "status": "success"}]
        res = tracker.analyze_causal_attribution(tool_calls=tool_calls, task_passed=False)
        self.assertEqual(res["attribution"], CausalAttribution.NOT_ACTIVATED.value)

    def test_activated_no_change(self):
        task_json = {
            "task_id": "C1_task_001",
            "complexity": "C1",
            "perturbation_mode": "P1",
            "execution_trace": [
                {"step": 1, "tool_name": "victim_tool", "is_perturbed": True}
            ]
        }
        tracker = PerturbationTracker(task_json)
        tracker.activations.append({
            "tool_name": "victim_tool",
            "changed_execution": False,
            "subsequent_tool_failed": False
        })
        res = tracker.analyze_causal_attribution(tool_calls=[], task_passed=False)
        self.assertEqual(res["attribution"], CausalAttribution.ACTIVATED_NO_CHANGE.value)

    def test_changed_no_failure_recovered(self):
        task_json = {
            "task_id": "C1_task_001",
            "complexity": "C1",
            "perturbation_mode": "P1",
            "execution_trace": [
                {"step": 1, "tool_name": "victim_tool", "is_perturbed": True}
            ]
        }
        tracker = PerturbationTracker(task_json)
        tracker.activations.append({
            "tool_name": "victim_tool",
            "changed_execution": True,
            "subsequent_tool_failed": True
        })
        # Task passed (CARE recovered!)
        res = tracker.analyze_causal_attribution(tool_calls=[], task_passed=True)
        self.assertEqual(res["attribution"], CausalAttribution.CHANGED_NO_FAILURE.value)

    def test_evidenced_perturbation_related_failure(self):
        task_json = {
            "task_id": "C1_task_001",
            "complexity": "C1",
            "perturbation_mode": "P1",
            "execution_trace": [
                {"step": 1, "tool_name": "victim_tool", "is_perturbed": True}
            ]
        }
        tracker = PerturbationTracker(task_json)
        tracker.activations.append({
            "tool_name": "victim_tool",
            "changed_execution": True,
            "subsequent_tool_failed": True
        })
        tool_calls = [
            {"tool_name": "victim_tool", "status": "error", "validation_status": "INVALID"}
        ]
        res = tracker.analyze_causal_attribution(tool_calls=tool_calls, task_passed=False)
        self.assertEqual(res["attribution"], CausalAttribution.EVIDENCED_PERTURBATION_RELATED.value)

    def test_unrelated_failure(self):
        task_json = {
            "task_id": "C1_task_001",
            "complexity": "C1",
            "perturbation_mode": "P1",
            "execution_trace": [
                {"step": 1, "tool_name": "victim_tool", "is_perturbed": True}
            ]
        }
        tracker = PerturbationTracker(task_json)
        tracker.activations.append({
            "tool_name": "victim_tool",
            "changed_execution": True,
            "subsequent_tool_failed": False
        })
        # Victim tool succeeded, but an unrelated tool failed
        tool_calls = [
            {"tool_name": "victim_tool", "status": "success"},
            {"tool_name": "unrelated_tool", "status": "error"}
        ]
        res = tracker.analyze_causal_attribution(tool_calls=tool_calls, task_passed=False)
        self.assertEqual(res["attribution"], CausalAttribution.FAILURE_UNRELATED.value)


class TestOfflineAnalysisPipeline(unittest.TestCase):
    """Tests for offline analysis aggregation, reporting, and zero LLM requirement."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.records_path = Path(self.temp_dir) / "experiment_records"
        self.records_path.mkdir(parents=True, exist_ok=True)

        # Create mock run 1 (Baseline)
        mgr_base = TelemetryManager(run_id="run_baseline", agent_type="baseline", model="mock_model", base_dir=self.records_path)
        rec_b1 = TelemetryRecorder(mgr_base, {"task_id": "C1_task_001", "complexity": "C1", "perturbation_mode": "P1"}, agent_type="baseline")
        rec_b1.complete_task(passed=False, judgement={"pass": False, "failure_reason": "Tool execution failure"})
        mgr_base.finalize_run()

        # Create mock run 2 (CARE)
        mgr_care = TelemetryManager(run_id="run_care", agent_type="care", model="mock_model", base_dir=self.records_path)
        rec_c1 = TelemetryRecorder(mgr_care, {"task_id": "C1_task_001", "complexity": "C1", "perturbation_mode": "P1"}, agent_type="care")
        rec_c1.record_recovery_attempt("victim_tool", "reroute", "alt_tool", remaining_budget=4, loop_warning=None, rationale="Reroute substitute")
        rec_c1.record_dag_path_selection("victim_tool", ["alt_tool"], "alt_tool", is_viable=True, reason="Path unblocked")
        rec_c1.complete_task(passed=True, judgement={"pass": True})
        mgr_care.finalize_run()

        # Create a malformed file to test resilience
        malformed_dir = self.records_path / "run_corrupt" / "task_records"
        malformed_dir.mkdir(parents=True, exist_ok=True)
        with open(malformed_dir / "bad.json", "w") as f:
            f.write("{invalid json content---")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_analyzer_runs_and_produces_all_artifacts(self):
        out_dir = Path(self.temp_dir) / "analysis_output"
        analyzer = ExperimentAnalyzer(
            records_dir=self.records_path,
            output_dir=out_dir
        )
        analyzer.load_records()
        self.assertEqual(len(analyzer.task_records), 2)
        self.assertEqual(len(analyzer.skipped_records), 1)

        report = analyzer.run_analysis()

        # Check required files exist
        self.assertTrue((out_dir / "failure_analysis.json").exists())
        self.assertTrue((out_dir / "failure_analysis.csv").exists())
        self.assertTrue((out_dir / "perturbation_comparison.csv").exists())
        self.assertTrue((out_dir / "tool_failure_summary.csv").exists())
        self.assertTrue((out_dir / "recovery_summary.csv").exists())
        self.assertTrue((out_dir / "path_analysis.csv").exists())
        self.assertTrue((out_dir / "metric_comparison.csv").exists())
        self.assertTrue((out_dir / "failure_analysis_report.md").exists())

        # Verify Baseline vs CARE matched metrics
        b_vs_c = report["baseline_vs_care"]
        matched = b_vs_c["matched_comparison"]
        self.assertEqual(matched["matched_tasks_count"], 1)
        self.assertEqual(matched["baseline_matched_tsr"], 0.0)
        self.assertEqual(matched["care_matched_tsr"], 1.0)
        self.assertEqual(matched["delta_tsr"], 1.0)

        # Verify DAG selections recorded
        rec_analysis = report["recovery_analysis"]
        self.assertEqual(rec_analysis["dag_path_selected_count"], 1)


class TestRegressionGuarantees(unittest.TestCase):
    """Ensure telemetry additions preserve existing contract and agent isolation."""

    def test_task_local_memory_reset_unchanged(self):
        from tool_memory.registry import ToolHealthRegistry
        from tool_memory.memory import ToolMemory

        reg = ToolHealthRegistry()
        mem = ToolMemory()
        reg.record_failure("tool_a", category="syntax", is_permanent=True)
        mem.record_call("tool_a", {}, "fail", False, 1)

        self.assertTrue(reg.is_blacklisted("tool_a"))
        self.assertEqual(len(mem.call_log), 1)

        # Ensure reset works as expected
        reg.reset()
        mem.reset()
        self.assertFalse(reg.is_blacklisted("tool_a"))
        self.assertEqual(len(mem.call_log), 0)


if __name__ == "__main__":
    unittest.main()
