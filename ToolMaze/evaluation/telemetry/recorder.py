"""
Telemetry Manager and Task Recorder for Persistent Storage.

Persists structured telemetry to:
ToolMaze/evaluation/experiment_records/<run_id>/
  - run_manifest.json
  - events.jsonl
  - task_records/<task_id>_<mode>.json
  - run_summary.json
  - failure_summary.json
"""

import os
import sys
import json
import uuid
import time
import threading
import datetime
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .schema import (
    TelemetryEvent,
    EventType,
    SCHEMA_VERSION,
    sanitize_and_redact,
    CausalAttribution
)
from .perturbation_tracker import PerturbationTracker

logger = logging.getLogger("Telemetry")


def get_project_root() -> Path:
    """Resolve ToolMaze project root safely from this file's location."""
    return Path(__file__).resolve().parent.parent.parent


def get_git_info() -> Dict[str, str]:
    """Inspect local git repository information safely without failing."""
    info = {"commit": "unknown", "branch": "unknown"}
    try:
        import subprocess
        root = get_project_root()
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            timeout=2
        ).decode().strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            stderr=subprocess.DEVNULL,
            timeout=2
        ).decode().strip()
        info["branch"] = branch
        info["commit"] = commit
    except Exception:
        pass
    return info


class TelemetryManager:
    """Manages the lifecycle and disk storage for an entire evaluation run."""

    def __init__(
        self,
        run_id: Optional[str] = None,
        agent_type: str = "care",
        model: str = "unknown_model",
        category: str = "c1",
        config: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None
    ):
        if run_id is None:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = uuid.uuid4().hex[:6]
            self.run_id = f"run_{ts}_{suffix}"
        else:
            self.run_id = run_id

        self.agent_type = agent_type
        self.model = model
        self.category = category
        self.config = config or {}

        # Resolve directory
        if base_dir:
            self.records_dir = Path(base_dir) / self.run_id
        else:
            self.records_dir = get_project_root() / "evaluation" / "experiment_records" / self.run_id

        self.task_records_dir = self.records_dir / "task_records"
        self.events_file = self.records_dir / "events.jsonl"
        self.manifest_file = self.records_dir / "run_manifest.json"
        self.summary_file = self.records_dir / "run_summary.json"
        self.failure_summary_file = self.records_dir / "failure_summary.json"

        # Create directories
        self.task_records_dir.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._sequence_counter = 0
        self.start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.git_info = get_git_info()

        # Write run manifest
        self._write_manifest()

        # Emit run_started event
        self.record_event(
            TelemetryEvent(
                run_id=self.run_id,
                task_id="GLOBAL",
                agent_type=self.agent_type,
                event_type=EventType.RUN_STARTED.value,
                component="runner",
                status="started",
                metadata={
                    "model": self.model,
                    "category": self.category,
                    "git": self.git_info
                }
            )
        )

    def _write_manifest(self) -> None:
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "agent_type": self.agent_type,
            "model": self.model,
            "category": self.category,
            "start_time": self.start_time,
            "git": self.git_info,
            "config": sanitize_and_redact(self.config)
        }
        try:
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write run_manifest.json: {e}")

    def record_event(self, event: TelemetryEvent) -> None:
        """Thread-safe append of an event to events.jsonl."""
        try:
            with self._lock:
                self._sequence_counter += 1
                if event.sequence_number == 0:
                    event.sequence_number = self._sequence_counter
                line = event.to_json() + "\n"
                with open(self.events_file, "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as e:
            logger.warning(f"Telemetry logging failed to append event: {e}")

    def save_task_record(self, task_record: Dict[str, Any]) -> Path:
        """Save durable task record to task_records/<task_id>_<mode>.json."""
        task_id = str(task_record.get("task_id", "unknown"))
        mode = str(task_record.get("mode", "P0"))
        # Safe filename
        safe_task_id = task_id.replace("/", "_").replace("\\", "_").replace(":", "_")
        filename = f"{safe_task_id}_{mode}.json"
        target_path = self.task_records_dir / filename

        sanitized = sanitize_and_redact(task_record)
        try:
            # Atomic write via tmp file
            tmp_path = target_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=2, ensure_ascii=False)
            if tmp_path.exists():
                os.replace(tmp_path, target_path)
        except Exception as e:
            logger.error(f"Failed to save task record for {filename}: {e}")
        return target_path

    def finalize_run(self, results: Optional[List[Dict[str, Any]]] = None) -> None:
        """Compute run summary, failure summary, and emit run_completed event."""
        end_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Collect all task record files written
        all_task_records = []
        try:
            for p in self.task_records_dir.glob("*.json"):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        all_task_records.append(json.load(f))
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Error reading task records during finalize: {e}")

        total_tasks = len(all_task_records)
        passed_tasks = sum(1 for t in all_task_records if t.get("passed") is True)
        failed_tasks = sum(1 for t in all_task_records if t.get("passed") is False)
        pass_rate = (passed_tasks / total_tasks) if total_tasks > 0 else 0.0

        run_summary = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.run_id,
            "agent_type": self.agent_type,
            "model": self.model,
            "category": self.category,
            "start_time": self.start_time,
            "end_time": end_time,
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "failed_tasks": failed_tasks,
            "pass_rate": pass_rate,
            "total_events": self._sequence_counter
        }

        # Breakdown by mode
        by_mode = {}
        for t in all_task_records:
            m = t.get("mode", "P0")
            if m not in by_mode:
                by_mode[m] = {"total": 0, "passed": 0, "failed": 0}
            by_mode[m]["total"] += 1
            if t.get("passed") is True:
                by_mode[m]["passed"] += 1
            else:
                by_mode[m]["failed"] += 1
        for m, stats in by_mode.items():
            stats["tsr"] = (stats["passed"] / stats["total"]) if stats["total"] > 0 else 0.0
        run_summary["modes"] = by_mode

        # Failure summary
        failures = []
        for t in all_task_records:
            if t.get("passed") is False:
                failures.append({
                    "task_id": t.get("task_id"),
                    "mode": t.get("mode"),
                    "causal_attribution": t.get("causal_attribution", {}).get("attribution"),
                    "attribution_confidence": t.get("causal_attribution", {}).get("confidence"),
                    "failure_reason": t.get("failure_reason"),
                    "failed_tools": t.get("failed_tools", []),
                    "recovery_attempts": len(t.get("recovery_events", []))
                })

        try:
            with open(self.summary_file, "w", encoding="utf-8") as f:
                json.dump(run_summary, f, indent=2, ensure_ascii=False)
            with open(self.failure_summary_file, "w", encoding="utf-8") as f:
                json.dump({"run_id": self.run_id, "failure_count": len(failures), "failures": failures}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write summaries: {e}")

        # Emit completion event
        self.record_event(
            TelemetryEvent(
                run_id=self.run_id,
                task_id="GLOBAL",
                agent_type=self.agent_type,
                event_type=EventType.RUN_COMPLETED.value,
                component="runner",
                status="completed",
                metadata={"total_tasks": total_tasks, "pass_rate": pass_rate}
            )
        )


class TelemetryRecorder:
    """Dedicated task-level telemetry recorder."""

    def __init__(
        self,
        manager: TelemetryManager,
        task_json: Dict[str, Any],
        agent_type: str = "care"
    ):
        self.manager = manager
        self.task_json = task_json
        self.task_id = str(task_json.get("task_id", "unknown_task"))
        self.complexity = str(task_json.get("complexity", "C1"))
        self.mode = str(task_json.get("perturbation_mode", "P0"))
        self.agent_type = agent_type

        self.start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.tracker = PerturbationTracker(task_json)

        self.events: List[TelemetryEvent] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.validation_records: List[Dict[str, Any]] = []
        self.diagnosis_records: List[Dict[str, Any]] = []
        self.recovery_records: List[Dict[str, Any]] = []
        self.dag_decisions: List[Dict[str, Any]] = []

        self.judgement: Optional[Dict[str, Any]] = None
        self.token_usage: Dict[str, int] = {}
        self.execution_status = "in_progress"

        # Emit task_started event
        self.emit_event(
            event_type=EventType.TASK_STARTED.value,
            component="execution_engine",
            status="started",
            metadata={
                "complexity": self.complexity,
                "mode": self.mode,
                "configured_perturbations": self.tracker.configured_perturbations
            }
        )

    def emit_event(
        self,
        event_type: str,
        component: str,
        status: str = "info",
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TelemetryEvent:
        """Create, store, and stream an event to the run manager."""
        try:
            event = TelemetryEvent(
                run_id=self.manager.run_id,
                task_id=self.task_id,
                agent_type=self.agent_type,
                event_type=event_type,
                component=component,
                status=status,
                duration_ms=duration_ms,
                metadata=metadata or {}
            )
            self.events.append(event)
            self.manager.record_event(event)
            return event
        except Exception as e:
            logger.warning(f"Error emitting telemetry event: {e}")
            return TelemetryEvent()

    def record_tool_call_start(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        call_index: int,
        step: int
    ) -> str:
        """Record beginning of a tool execution."""
        call_id = f"tc_{step}_{call_index}_{tool_name}"
        self.emit_event(
            event_type=EventType.TOOL_CALL_STARTED.value,
            component="tool_executor",
            status="invoked",
            metadata={
                "call_id": call_id,
                "tool_name": tool_name,
                "call_index": call_index,
                "step": step,
                "arguments": sanitize_and_redact(arguments)
            }
        )
        return call_id

    def record_tool_call_completion(
        self,
        call_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        raw_result: Any,
        status: str,
        duration_ms: float,
        perturbation_status: str,
        validation_result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> None:
        """Record completed tool call with full outcome classification."""
        is_perturbed = (perturbation_status == "perturbed")

        # Check if output is error
        has_error = (status == "error") or (isinstance(raw_result, dict) and "error" in raw_result)
        val_status = "UNKNOWN"
        val_passed = None
        if validation_result:
            val_status = validation_result.get("pipeline_status", "UNKNOWN")
            val_passed = (val_status == "VALID")

        tool_record = {
            "call_id": call_id,
            "tool_name": tool_name,
            "arguments": sanitize_and_redact(arguments),
            "result_sample": sanitize_and_redact(raw_result),
            "status": status,
            "duration_ms": duration_ms,
            "perturbation_status": perturbation_status,
            "is_perturbed": is_perturbed,
            "validation_status": val_status,
            "validation_passed": val_passed,
            "has_error": has_error,
            "error_message": error_message,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.tool_calls.append(tool_record)

        # Perturbation tracking if perturbed
        if is_perturbed:
            act_record = self.tracker.record_activation(
                tool_name=tool_name,
                arguments=arguments,
                modified_output=raw_result,
                status=status,
                step=len(self.tool_calls),
                timestamp=tool_record["timestamp"]
            )
            self.emit_event(
                event_type=EventType.PERTURBATION_ACTIVATED.value,
                component="sandbox",
                status="activated",
                metadata=act_record
            )

        # Emit completion or failure event
        evt_type = EventType.TOOL_CALL_FAILED.value if has_error else EventType.TOOL_CALL_COMPLETED.value
        self.emit_event(
            event_type=evt_type,
            component="tool_executor",
            status="error" if has_error else "success",
            duration_ms=duration_ms,
            metadata=tool_record
        )

        if validation_result:
            self.record_validation(call_id, tool_name, validation_result)

    def record_validation(
        self,
        call_id: str,
        tool_name: str,
        validation_result: Dict[str, Any]
    ) -> None:
        """Record deterministic semantic output validation."""
        val_data = {
            "call_id": call_id,
            "tool_name": tool_name,
            "pipeline_status": validation_result.get("pipeline_status"),
            "checks": sanitize_and_redact(validation_result.get("checks", {})),
            "failed_checks": sanitize_and_redact(validation_result.get("failed_checks", {})),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.validation_records.append(val_data)
        self.emit_event(
            event_type=EventType.VALIDATION_COMPLETED.value,
            component="semantic_validation",
            status=val_data["pipeline_status"] or "UNKNOWN",
            metadata=val_data
        )

    def record_diagnosis(
        self,
        tool_name: str,
        category: str,
        persistence: str,
        root_cause: str,
        severity: str,
        recommended_action: str,
        evidence: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record structured failure diagnosis from Layer 2."""
        diag_data = {
            "tool_name": tool_name,
            "category": category,
            "persistence": persistence,
            "root_cause": root_cause,
            "severity": severity,
            "recommended_action": recommended_action,
            "evidence": sanitize_and_redact(evidence or {}),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.diagnosis_records.append(diag_data)
        self.emit_event(
            event_type=EventType.DIAGNOSIS_COMPLETED.value,
            component="diagnosis_engine",
            status=category,
            metadata=diag_data
        )

    def record_recovery_attempt(
        self,
        failed_tool: str,
        action: str,
        suggested_tool: Optional[str],
        remaining_budget: Optional[int],
        loop_warning: Optional[str],
        rationale: str
    ) -> None:
        """Record recovery controller decision from Layer 3/6."""
        rec_data = {
            "failed_tool": failed_tool,
            "action": action,
            "suggested_tool": suggested_tool,
            "remaining_budget": remaining_budget,
            "loop_warning": loop_warning,
            "rationale": rationale,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.recovery_records.append(rec_data)
        self.emit_event(
            event_type=EventType.RECOVERY_STARTED.value,
            component="recovery_controller",
            status=action,
            metadata=rec_data
        )

    def record_dag_path_selection(
        self,
        failed_tool: str,
        candidate_tools: List[str],
        selected_tool: Optional[str],
        is_viable: bool,
        reason: str,
        target_path: Optional[List[str]] = None
    ) -> None:
        """Record DAG path selection decision from Layer 4."""
        dag_data = {
            "failed_tool": failed_tool,
            "candidate_tools": candidate_tools,
            "selected_tool": selected_tool,
            "is_viable": is_viable,
            "reason": reason,
            "target_path": target_path,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.dag_decisions.append(dag_data)
        self.emit_event(
            event_type=EventType.PATH_SELECTED.value if is_viable else EventType.PATH_PRUNED.value,
            component="dag_path_selector",
            status="selected" if is_viable else "blocked",
            metadata=dag_data
        )

    def complete_task(
        self,
        passed: Optional[bool] = None,
        judgement: Optional[Dict[str, Any]] = None,
        token_usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None
    ) -> Path:
        """Finalize the task record, compute causal attribution, emit task_completed, and write file."""
        self.execution_status = "completed" if error is None else "failed"
        self.judgement = judgement
        self.token_usage = token_usage or {}

        # Determine pass/fail
        task_passed = passed
        if task_passed is None and judgement:
            task_passed = judgement.get("pass", False)

        # Causal attribution analysis
        attribution = self.tracker.analyze_causal_attribution(
            tool_calls=self.tool_calls,
            task_passed=task_passed
        )

        failed_tools = list({
            tc["tool_name"] for tc in self.tool_calls
            if tc.get("status") == "error" or tc.get("validation_status") == "INVALID"
        })

        # Assemble full task record
        record = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.manager.run_id,
            "task_id": self.task_id,
            "mode": self.mode,
            "complexity": self.complexity,
            "task_definition": self.task_json,
            "agent_type": self.agent_type,
            "model": self.manager.model,
            "start_time": self.start_time,
            "end_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": self.execution_status,
            "passed": task_passed,
            "error": error,
            "failure_reason": judgement.get("failure_reason") if judgement else error,
            "failed_tools": failed_tools,
            "tokens": self.token_usage,
            "parameters": {
                "user_input": self.task_json.get("user_input", {}),
                "task_description": self.task_json.get("task_description", ""),
                "template_id": self.task_json.get("template_id"),
                "domains": self.task_json.get("domains", []),
                "execution": self.manager.config.get("execution", {}),
                "agent_config": {
                    "model": self.manager.model,
                    "temperature": self.manager.config.get("agent", {}).get("temperature"),
                    "max_tokens": self.manager.config.get("agent", {}).get("max_tokens")
                }
            },
            "causal_attribution": attribution,
            "perturbation_tracking": {
                "configured": self.tracker.configured_perturbations,
                "activations": self.tracker.activations
            },
            "tool_calls": self.tool_calls,
            "validations": self.validation_records,
            "diagnoses": self.diagnosis_records,
            "recovery_events": self.recovery_records,
            "dag_decisions": self.dag_decisions,
            "judgement": self.judgement
        }

        # Emit event
        evt_type = EventType.TASK_COMPLETED.value if (task_passed is not False and error is None) else EventType.TASK_FAILED.value
        self.emit_event(
            event_type=evt_type,
            component="runner",
            status="pass" if task_passed else "fail",
            metadata={
                "passed": task_passed,
                "attribution": attribution["attribution"],
                "tool_calls_count": len(self.tool_calls)
            }
        )

        # Persist task record
        return self.manager.save_task_record(record)
