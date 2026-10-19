"""
Perturbation Tracker and Causal Attribution Module.

Extracts ground-truth perturbation specifications from task definitions across
C1 (single trace), C2/C3 (per-path maps), and C4 (per-slot first touch),
tracks live activation state, detects whether output was modified, and correlates
with subsequent tool or task failures.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
from .schema import CausalAttribution, sanitize_and_redact


class PerturbationTracker:
    """Tracks configured vs activated perturbations for a single task."""

    def __init__(self, task_json: Dict[str, Any]):
        self.task_json = task_json
        self.task_id = str(task_json.get("task_id", "unknown_task"))
        self.complexity = str(task_json.get("complexity", "C1"))
        self.mode = str(task_json.get("perturbation_mode", "P0"))
        self.perturbation_point = task_json.get("perturbation_point")
        self.template_id = task_json.get("template_id")

        # Discover configured perturbations from task_json
        self.configured_perturbations = self._extract_configured_perturbations()
        self.activations: List[Dict[str, Any]] = []

    def _extract_configured_perturbations(self) -> List[Dict[str, Any]]:
        """Extract explicit perturbation definitions from task_json."""
        if self.mode == "P0":
            return []

        specs = []
        # Check C1 style: single execution_trace
        exec_trace = self.task_json.get("execution_trace", [])
        if exec_trace:
            for step in exec_trace:
                if step.get("is_perturbed"):
                    specs.append({
                        "config_id": f"{self.task_id}_step_{step.get('step')}_{step.get('tool_name')}",
                        "target_tool": step.get("tool_name"),
                        "step": step.get("step"),
                        "mode": self.mode,
                        "complexity": self.complexity,
                        "expected_status": step.get("status", "error"),
                        "ground_truth_output": step.get("output"),
                        "error_message": step.get("error_message"),
                        "trigger_condition": "first_call" if self.mode in ("P1", "P3") else "all_calls",
                        "category": "syntactic" if self.mode in ("P1", "P2") else "semantic",
                        "source_path": None,
                    })

        # Check C2 / C3 / C4 style: valid_paths
        valid_paths = self.task_json.get("valid_paths", [])
        for vp in valid_paths:
            path_id = vp.get("path_id", "path_unknown")
            group_choices = vp.get("group_choices", [])
            for step in vp.get("execution_trace", []):
                if step.get("is_perturbed"):
                    tool_name = step.get("tool_name")
                    specs.append({
                        "config_id": f"{self.task_id}_{path_id}_{tool_name}",
                        "target_tool": tool_name,
                        "step": step.get("step"),
                        "mode": self.mode,
                        "complexity": self.complexity,
                        "expected_status": step.get("status", "error"),
                        "ground_truth_output": step.get("output"),
                        "error_message": step.get("error_message"),
                        "trigger_condition": "first_touch_path" if self.complexity in ("C2", "C3") else "first_touch_slot",
                        "category": "syntactic" if self.mode in ("P1", "P2") else "semantic",
                        "source_path": path_id,
                        "group_choices": group_choices
                    })

        # Deduplicate while preserving details
        unique_specs = []
        seen_keys = set()
        for s in specs:
            k = (s["target_tool"], s.get("source_path"))
            if k not in seen_keys:
                seen_keys.add(k)
                unique_specs.append(s)

        return unique_specs

    def record_activation(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        modified_output: Any,
        status: str,
        step: int,
        timestamp: str
    ) -> Dict[str, Any]:
        """Record an instance where a perturbation was actually activated and injected."""
        matching_config = None
        for cfg in self.configured_perturbations:
            if cfg["target_tool"] == tool_name:
                matching_config = cfg
                break

        record = {
            "activation_id": f"act_{len(self.activations) + 1}_{tool_name}",
            "tool_name": tool_name,
            "step": step,
            "timestamp": timestamp,
            "config_id": matching_config["config_id"] if matching_config else f"unknown_cfg_{tool_name}",
            "configured_mode": self.mode,
            "changed_execution": True,
            "modified_status": status,
            "arguments_sample": sanitize_and_redact(arguments),
            "modified_output_sample": sanitize_and_redact(modified_output),
            "subsequent_tool_failed": (status == "error") or (isinstance(modified_output, dict) and "error" in modified_output),
            "recovered": False
        }
        self.activations.append(record)
        return record

    def analyze_causal_attribution(
        self,
        tool_calls: List[Dict[str, Any]],
        task_passed: Optional[bool]
    ) -> Dict[str, Any]:
        """Classify the causal link between configured perturbations and observed outcome."""
        if self.mode == "P0" or not self.configured_perturbations:
            return {
                "attribution": CausalAttribution.NOT_ACTIVATED.value,
                "confidence": "HIGH",
                "evidence": "Task is P0 or has no configured perturbations.",
                "configured_count": 0,
                "activated_count": 0,
                "recovered_count": 0
            }

        activated_count = len(self.activations)
        if activated_count == 0:
            return {
                "attribution": CausalAttribution.NOT_ACTIVATED.value,
                "confidence": "HIGH",
                "evidence": f"Mode {self.mode} configured for tools {[c['target_tool'] for c in self.configured_perturbations]}, but agent never invoked victim tool.",
                "configured_count": len(self.configured_perturbations),
                "activated_count": 0,
                "recovered_count": 0
            }

        # Check if the activated perturbation changed output
        all_changed = all(a.get("changed_execution", False) for a in self.activations)
        if not all_changed:
            return {
                "attribution": CausalAttribution.ACTIVATED_NO_CHANGE.value,
                "confidence": "MEDIUM",
                "evidence": "Perturbation was triggered but caused no detectable modification to tool output.",
                "configured_count": len(self.configured_perturbations),
                "activated_count": activated_count,
                "recovered_count": 0
            }

        # Check subsequent calls and outcome
        if task_passed is True:
            return {
                "attribution": CausalAttribution.CHANGED_NO_FAILURE.value,
                "confidence": "HIGH",
                "evidence": f"Perturbation altered output of {self.activations[0]['tool_name']}, but task ultimately succeeded (successful recovery or bypass).",
                "configured_count": len(self.configured_perturbations),
                "activated_count": activated_count,
                "recovered_count": activated_count
            }

        # Task failed or had tool failure: distinguish evidenced perturbation failure from unrelated failure
        # Look for explicit failure on the perturbed tool
        has_perturbed_failure = any(
            a.get("subsequent_tool_failed", False) for a in self.activations
        )

        # Look at the tool calls that actually failed
        failed_tools = [
            tc.get("tool_name") for tc in tool_calls
            if tc.get("status") == "error" or tc.get("validation_status") == "INVALID"
        ]

        perturbed_tools = {a["tool_name"] for a in self.activations}
        matching_failures = [t for t in failed_tools if t in perturbed_tools]

        if matching_failures or has_perturbed_failure:
            return {
                "attribution": CausalAttribution.EVIDENCED_PERTURBATION_RELATED.value,
                "confidence": "HIGH",
                "evidence": f"Perturbation modified tool {list(perturbed_tools)}, matching recorded execution failure in tools {matching_failures or list(perturbed_tools)} leading to task failure.",
                "configured_count": len(self.configured_perturbations),
                "activated_count": activated_count,
                "recovered_count": 0
            }

        if failed_tools and not any(t in perturbed_tools for t in failed_tools):
            return {
                "attribution": CausalAttribution.FAILURE_UNRELATED.value,
                "confidence": "MEDIUM",
                "evidence": f"Perturbation affected {list(perturbed_tools)}, but failures occurred on unrelated tools: {failed_tools}.",
                "configured_count": len(self.configured_perturbations),
                "activated_count": activated_count,
                "recovered_count": 0
            }

        return {
            "attribution": CausalAttribution.CHANGED_FAILURE_UNCERTAIN.value,
            "confidence": "LOW",
            "evidence": "Perturbation was injected and task failed, but causal chain lacks definitive link.",
            "configured_count": len(self.configured_perturbations),
            "activated_count": activated_count,
            "recovered_count": 0
        }
