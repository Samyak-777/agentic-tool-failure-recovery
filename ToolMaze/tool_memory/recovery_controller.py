"""
Recovery Controller for Layer 3.
Translates Layer 2 Structured Diagnosis, Layer 3 Memory/Budget State,
Layer 4 DAG Path Selection, and Layer 6 Loop Detection into concrete recovery directives.
"""

from typing import Dict, Any, List, Optional, Set
from diagnosis.taxonomy import (
    StructuredDiagnosis,
    PersistenceType,
    RecoveryDirective,
    FailureCategory
)
from .registry import ToolHealthRegistry, ToolHealthStatus
from .memory import ToolMemory
from .budget import BudgetTracker, BudgetConfig
from .loop_detector import LoopDetector, LoopCheckResult

try:
    from dag_rerouting.path_selector import DAGPathSelector, RerouteCandidate
except ImportError:
    try:
        from ..dag_rerouting.path_selector import DAGPathSelector, RerouteCandidate
    except ImportError:
        DAGPathSelector = None
        RerouteCandidate = None


class RecoveryController:
    """Orchestrates recovery decisions based on Diagnosis, Memory, Budget, DAG, and Loops."""

    def __init__(
        self,
        health_registry: Optional[ToolHealthRegistry] = None,
        memory: Optional[ToolMemory] = None,
        budget_tracker: Optional[BudgetTracker] = None,
        alternative_tools_map: Optional[Dict[str, List[str]]] = None,
        path_selector: Optional[Any] = None,
        loop_detector: Optional[LoopDetector] = None
    ):
        self.registry = health_registry or ToolHealthRegistry()
        self.memory = memory or ToolMemory()
        self.budget = budget_tracker or BudgetTracker()
        self.alternative_map = alternative_tools_map or {}
        self.path_selector = path_selector or (DAGPathSelector() if DAGPathSelector else None)
        self.loop_detector = loop_detector or LoopDetector()

    def decide_recovery(
        self,
        diagnosis: StructuredDiagnosis,
        arguments: Dict[str, Any],
        step_num: int,
        task_json: Optional[Dict[str, Any]] = None,
        executed_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compute the recovery action and instructions for the agent.
        
        Returns:
            Dict containing:
                - "action": "continue" | "retry" | "verify" | "reroute" | "abort"
                - "suggested_tool": str or None
                - "rationale": str
                - "agent_prompt_guidance": str
                - "loop_warning": str or None
        """
        tool_name = diagnosis.tool_name
        exec_tools = executed_tools or self.memory.get_executed_tools()

        # 0. Check Loop / Ping-Pong Detection (Layer 6)
        loop_res = self.loop_detector.record_call(tool_name, arguments, is_valid=diagnosis.is_valid)
        loop_warning = loop_res.warning_message if loop_res.is_loop else None

        if loop_res.is_loop:
            if loop_res.suggested_action == "abort":
                return {
                    "action": RecoveryDirective.ABORT.value,
                    "suggested_tool": None,
                    "rationale": f"Cyclic deadlock detected ({loop_res.loop_type}). Recovery aborted.",
                    "agent_prompt_guidance": loop_res.warning_message,
                    "loop_warning": loop_warning
                }
            elif loop_res.suggested_action == "blacklist_and_reroute":
                # Force blacklist on looping tool to break cycle
                self.registry.record_failure(tool_name, category="loop_deadlock", is_permanent=True)

        # 1. If valid -> Continue
        if diagnosis.is_valid and not loop_res.is_loop:
            self.registry.record_success(tool_name)
            self.memory.record_call(tool_name, arguments, output="success", is_valid=True, step_num=step_num)
            self.budget.record_tool_call(tool_name, is_recovery=False)
            return {
                "action": RecoveryDirective.CONTINUE.value,
                "suggested_tool": tool_name,
                "rationale": "Tool executed cleanly; passed all deterministic checks.",
                "agent_prompt_guidance": "",
                "loop_warning": None
            }

        # 2. Record failure in Registry & Memory
        is_permanent = (diagnosis.persistence == PersistenceType.PERMANENT) or loop_res.is_loop
        self.registry.record_failure(tool_name, category=diagnosis.category.value, is_permanent=is_permanent)
        self.memory.record_call(tool_name, arguments, output=diagnosis.raw_error, is_valid=False, step_num=step_num)
        self.budget.record_tool_call(tool_name, is_recovery=True)

        # 3. Check Budget Exceeded
        if not self.budget.has_recovery_budget():
            return {
                "action": RecoveryDirective.ABORT.value,
                "suggested_tool": None,
                "rationale": "Recovery budget exhausted. Further recovery calls blocked.",
                "agent_prompt_guidance": (
                    "CRITICAL: Recovery budget exceeded. Do not attempt further tool calls. "
                    "Formulate your best final answer based on already verified outputs."
                ),
                "loop_warning": loop_warning
            }

        # 4. Check Blacklist Status (Permanent failure or cycle-broken tool)
        if self.registry.is_blacklisted(tool_name):
            alt_tool, alt_reason = self._find_healthy_alternative(tool_name, task_json, exec_tools)
            if alt_tool:
                return {
                    "action": RecoveryDirective.REROUTE.value,
                    "suggested_tool": alt_tool,
                    "rationale": f"Tool '{tool_name}' is blacklisted ({self.registry.get_record(tool_name).blacklist_reason}). Rerouting: {alt_reason}",
                    "agent_prompt_guidance": (
                        f"SYSTEM ALERT: Tool '{tool_name}' is permanently unavailable or corrupted. "
                        f"Switch immediately to alternative tool '{alt_tool}'."
                    ),
                    "loop_warning": loop_warning
                }
            else:
                return {
                    "action": RecoveryDirective.ABORT.value,
                    "suggested_tool": None,
                    "rationale": f"Tool '{tool_name}' is blacklisted and no healthy alternatives exist in DAG.",
                    "agent_prompt_guidance": (
                        f"SYSTEM ALERT: Tool '{tool_name}' has failed permanently and no alternative tools exist. "
                        "Abort the path and summarize findings."
                    ),
                    "loop_warning": loop_warning
                }

        # 5. Check if Transient -> Retry (unless blocked by loop detection)
        if diagnosis.persistence == PersistenceType.TRANSIENT and not loop_res.is_loop:
            if self.budget.can_retry_tool(tool_name):
                return {
                    "action": RecoveryDirective.RETRY.value,
                    "suggested_tool": tool_name,
                    "rationale": f"Transient failure detected on '{tool_name}'. Budget allows retry.",
                    "agent_prompt_guidance": (
                        f"RETRY DIRECTIVE: Tool '{tool_name}' experienced a transient anomaly ({diagnosis.root_cause}). "
                        "Retry this tool call once with verified parameters."
                    ),
                    "loop_warning": None
                }
            else:
                # Retry budget for this tool reached -> Reroute
                alt_tool, alt_reason = self._find_healthy_alternative(tool_name, task_json, exec_tools)
                if alt_tool:
                    return {
                        "action": RecoveryDirective.REROUTE.value,
                        "suggested_tool": alt_tool,
                        "rationale": f"Retry budget for '{tool_name}' reached. Switching to '{alt_tool}' ({alt_reason}).",
                        "agent_prompt_guidance": f"Retry limit reached for '{tool_name}'. Switch to alternative '{alt_tool}'.",
                        "loop_warning": loop_warning
                    }
                else:
                    return {
                        "action": RecoveryDirective.ABORT.value,
                        "suggested_tool": None,
                        "rationale": f"Retry budget for '{tool_name}' reached and no alternatives available.",
                        "agent_prompt_guidance": f"Unable to recover '{tool_name}'. Proceed with graceful fallback.",
                        "loop_warning": loop_warning
                    }

        # 6. Default Fallback -> Reroute
        alt_tool, alt_reason = self._find_healthy_alternative(tool_name, task_json, exec_tools)
        if alt_tool:
            return {
                "action": RecoveryDirective.REROUTE.value,
                "suggested_tool": alt_tool,
                "rationale": f"Rerouting from '{tool_name}' to '{alt_tool}' ({alt_reason}).",
                "agent_prompt_guidance": f"Switch to substitute tool '{alt_tool}'.",
                "loop_warning": loop_warning
            }

        return {
            "action": RecoveryDirective.ABORT.value,
            "suggested_tool": None,
            "rationale": "No viable recovery path identified.",
            "agent_prompt_guidance": "No viable alternative found. Abort recovery.",
            "loop_warning": loop_warning
        }

    def _find_healthy_alternative(
        self,
        tool_name: str,
        task_json: Optional[Dict[str, Any]] = None,
        executed_tools: Optional[List[str]] = None
    ) -> tuple[Optional[str], str]:
        """Find an alternative tool that is not blacklisted using DAGPathSelector or lookup map."""
        blacklisted = self.registry.get_blacklisted_tools()
        exec_tools = executed_tools or []

        # Layer 4: Use DAGPathSelector if available
        if self.path_selector and task_json:
            candidate = self.path_selector.find_reroute(
                failed_tool=tool_name,
                task_json=task_json,
                blacklisted_tools=blacklisted,
                executed_tools=exec_tools
            )
            if candidate.is_viable and candidate.selected_tool:
                return candidate.selected_tool, candidate.reason

        # Fallback: Dictionary lookup
        candidates = self.alternative_map.get(tool_name, [])
        for cand in candidates:
            if not self.registry.is_blacklisted(cand):
                return cand, "Selected from static alternative map."

        return None, "No candidate alternatives found."

    def reset(self):
        self.registry.reset()
        self.memory.reset()
        self.budget.reset()
        self.loop_detector.reset()
