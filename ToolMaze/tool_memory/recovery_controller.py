"""
Recovery Controller for Layer 3.
Translates Layer 2 Structured Diagnosis and Layer 3 Memory/Budget State
into concrete recovery directives: Retry, Verify, Reroute, Abort.
"""

from typing import Dict, Any, List, Optional
from diagnosis.taxonomy import (
    StructuredDiagnosis,
    PersistenceType,
    RecoveryDirective,
    FailureCategory
)
from .registry import ToolHealthRegistry, ToolHealthStatus
from .memory import ToolMemory
from .budget import BudgetTracker, BudgetConfig

class RecoveryController:
    """Orchestrates recovery decisions based on Diagnosis, Memory, and Budget."""

    def __init__(
        self,
        health_registry: Optional[ToolHealthRegistry] = None,
        memory: Optional[ToolMemory] = None,
        budget_tracker: Optional[BudgetTracker] = None,
        alternative_tools_map: Optional[Dict[str, List[str]]] = None
    ):
        self.registry = health_registry or ToolHealthRegistry()
        self.memory = memory or ToolMemory()
        self.budget = budget_tracker or BudgetTracker()
        self.alternative_map = alternative_tools_map or {}

    def decide_recovery(
        self,
        diagnosis: StructuredDiagnosis,
        arguments: Dict[str, Any],
        step_num: int
    ) -> Dict[str, Any]:
        """Compute the recovery action and instructions for the agent.
        
        Returns:
            Dict containing:
                - "action": "continue" | "retry" | "verify" | "reroute" | "abort"
                - "suggested_tool": str or None
                - "rationale": str
                - "agent_prompt_guidance": str
        """
        tool_name = diagnosis.tool_name

        # 1. If valid -> Continue
        if diagnosis.is_valid:
            self.registry.record_success(tool_name)
            self.memory.record_call(tool_name, arguments, output="success", is_valid=True, step_num=step_num)
            self.budget.record_tool_call(tool_name, is_recovery=False)
            return {
                "action": RecoveryDirective.CONTINUE.value,
                "suggested_tool": tool_name,
                "rationale": "Tool executed cleanly; passed all deterministic checks.",
                "agent_prompt_guidance": ""
            }

        # 2. Record failure in Registry & Memory
        is_permanent = (diagnosis.persistence == PersistenceType.PERMANENT)
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
                )
            }

        # 4. Check Blacklist Status
        if self.registry.is_blacklisted(tool_name):
            # Must Reroute or Abort
            alt_tool = self._find_healthy_alternative(tool_name)
            if alt_tool:
                return {
                    "action": RecoveryDirective.REROUTE.value,
                    "suggested_tool": alt_tool,
                    "rationale": f"Tool '{tool_name}' is blacklisted ({self.registry.get_record(tool_name).blacklist_reason}). Rerouting to substitute '{alt_tool}'.",
                    "agent_prompt_guidance": (
                        f"SYSTEM ALERT: Tool '{tool_name}' is permanently unavailable or produces corrupted outputs. "
                        f"Switch immediately to alternative tool '{alt_tool}'."
                    )
                }
            else:
                return {
                    "action": RecoveryDirective.ABORT.value,
                    "suggested_tool": None,
                    "rationale": f"Tool '{tool_name}' is blacklisted and no healthy alternatives exist in DAG.",
                    "agent_prompt_guidance": (
                        f"SYSTEM ALERT: Tool '{tool_name}' has failed permanently and no alternative tools exist. "
                        "Abort the path and summarize findings."
                    )
                }

        # 5. Check if Transient -> Retry
        if diagnosis.persistence == PersistenceType.TRANSIENT:
            if self.budget.can_retry_tool(tool_name):
                return {
                    "action": RecoveryDirective.RETRY.value,
                    "suggested_tool": tool_name,
                    "rationale": f"Transient failure detected on '{tool_name}'. Budget allows retry.",
                    "agent_prompt_guidance": (
                        f"RETRY DIRECTIVE: Tool '{tool_name}' experienced a transient anomaly ({diagnosis.root_cause}). "
                        "Retry this tool call once with verified parameters."
                    )
                }
            else:
                # Retry budget for this tool reached -> Reroute
                alt_tool = self._find_healthy_alternative(tool_name)
                if alt_tool:
                    return {
                        "action": RecoveryDirective.REROUTE.value,
                        "suggested_tool": alt_tool,
                        "rationale": f"Retry budget for '{tool_name}' reached. Switching to '{alt_tool}'.",
                        "agent_prompt_guidance": f"Retry limit reached for '{tool_name}'. Switch to alternative '{alt_tool}'."
                    }
                else:
                    return {
                        "action": RecoveryDirective.ABORT.value,
                        "suggested_tool": None,
                        "rationale": f"Retry budget for '{tool_name}' reached and no alternatives available.",
                        "agent_prompt_guidance": f"Unable to recover '{tool_name}'. Proceed with graceful fallback."
                    }

        # 6. Default Fallback -> Reroute
        alt_tool = self._find_healthy_alternative(tool_name)
        if alt_tool:
            return {
                "action": RecoveryDirective.REROUTE.value,
                "suggested_tool": alt_tool,
                "rationale": f"Rerouting from '{tool_name}' to '{alt_tool}'.",
                "agent_prompt_guidance": f"Switch to substitute tool '{alt_tool}'."
            }

        return {
            "action": RecoveryDirective.ABORT.value,
            "suggested_tool": None,
            "rationale": "No viable recovery path identified.",
            "agent_prompt_guidance": "No viable alternative found. Abort recovery."
        }

    def _find_healthy_alternative(self, tool_name: str) -> Optional[str]:
        """Find an alternative tool that is not blacklisted."""
        candidates = self.alternative_map.get(tool_name, [])
        for cand in candidates:
            if not self.registry.is_blacklisted(cand):
                return cand
        return None

    def reset(self):
        self.registry.reset()
        self.memory.reset()
        self.budget.reset()
