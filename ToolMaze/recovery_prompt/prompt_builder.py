"""
ToolMaze/recovery_prompt/prompt_builder.py
Layer 5: Dynamic Recovery Prompts with Evidence

Constructs structured, evidence-grounded prompt interventions for LLM agents,
replacing uninformative generic errors with actionable diagnostic directives.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from diagnosis.taxonomy import StructuredDiagnosis, PersistenceType, RecoveryDirective


@dataclass
class RecoveryPromptPayload:
    """Structured recovery payload provided to the agent."""
    action: str
    failed_tool: str
    diagnosis_category: str
    root_cause: str
    persistence: str
    is_blacklisted: bool
    blacklisted_tools: List[str] = field(default_factory=list)
    suggested_substitute: Optional[str] = None
    remaining_recovery_budget: Optional[int] = None
    prompt_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "failed_tool": self.failed_tool,
            "diagnosis_category": self.diagnosis_category,
            "root_cause": self.root_cause,
            "persistence": self.persistence,
            "is_blacklisted": self.is_blacklisted,
            "blacklisted_tools": self.blacklisted_tools,
            "suggested_substitute": self.suggested_substitute,
            "remaining_recovery_budget": self.remaining_recovery_budget,
            "prompt_text": self.prompt_text,
        }


class DynamicRecoveryPromptBuilder:
    """Builds evidence-based prompt messages that guide the agent through recovery."""

    def __init__(self, include_detailed_evidence: bool = True):
        self.include_detailed_evidence = include_detailed_evidence

    def build_prompt(
        self,
        diagnosis: StructuredDiagnosis,
        recovery_decision: Dict[str, Any],
        blacklisted_tools: Optional[Set[str]] = None,
        remaining_budget: Optional[int] = None,
        loop_warning: Optional[str] = None
    ) -> RecoveryPromptPayload:
        """Generate a complete structured recovery prompt for the agent.
        
        Args:
            diagnosis: The Layer 2 StructuredDiagnosis object.
            recovery_decision: The Layer 3/4 recovery decision dict.
            blacklisted_tools: Currently blacklisted tools in this session.
            remaining_budget: Remaining tool call allowance for recovery.
            loop_warning: Optional loop detection alert.
        """
        action = recovery_decision.get("action", "retry").upper()
        tool_name = diagnosis.tool_name
        suggested_tool = recovery_decision.get("suggested_tool")
        blacklist_list = sorted(list(blacklisted_tools or set()))
        is_blacklisted = tool_name in (blacklisted_tools or set())

        lines: List[str] = []
        lines.append(f"=== [CARE RECOVERY ORCHESTRATOR: {action}] ===")
        
        # 1. State Diagnosis & Evidence
        lines.append(f"Target Tool: {tool_name}")
        lines.append(f"Status: ANOMALY DETECTED (Category: {diagnosis.category.value})")
        lines.append(f"Root Cause: {diagnosis.root_cause}")
        lines.append(f"Persistence Assessment: {diagnosis.persistence.value}")

        if self.include_detailed_evidence and diagnosis.violations:
            violation_strs = [
                f"{v.checker_name}: {v.message}"
                for v in diagnosis.violations[:3]
            ]
            lines.append("Violations: " + "; ".join(violation_strs))

        # 2. Tool Health & Blacklist Awareness
        if blacklist_list:
            lines.append(f"Blacklisted Tools (DO NOT CALL): {blacklist_list}")

        # 3. Budget Status
        if remaining_budget is not None:
            lines.append(f"Remaining Recovery Budget: {remaining_budget} calls")

        # 4. Loop Warning (if any)
        if loop_warning:
            lines.append(f"WARNING: {loop_warning}")

        # 5. Concrete Action Directives
        lines.append("--- INSTRUCTION ---")
        if action == RecoveryDirective.RETRY.value.upper():
            lines.append(
                f"ACTION: RETRY tool '{tool_name}' with verified parameters. "
                "This anomaly is classified as TRANSIENT (e.g. temporary glitch or rate limit). "
                "Do NOT abandon the current path yet."
            )
        elif action == RecoveryDirective.REROUTE.value.upper():
            if suggested_tool:
                lines.append(
                    f"ACTION: REROUTE immediately. Tool '{tool_name}' has failed permanently and is BLOCKED. "
                    f"You MUST use alternative tool '{suggested_tool}'. "
                    f"Do NOT call '{tool_name}' or any blacklisted tools again."
                )
            else:
                lines.append(
                    f"ACTION: REROUTE. Tool '{tool_name}' is permanently unavailable. "
                    "Explore an alternative unvisited branch in your available tools."
                )
        elif action == RecoveryDirective.VERIFY.value.upper():
            lines.append(
                f"ACTION: VERIFY. The output from '{tool_name}' contains suspicious semantic attributes. "
                "Inspect the fields or query an auxiliary verification check before proceeding."
            )
        elif action == RecoveryDirective.ABORT.value.upper():
            lines.append(
                "ACTION: ABORT CURRENT TOOL CHAIN. Recovery budget is exhausted or all valid solution paths are blocked. "
                "Do NOT invoke further tools. Synthesize and deliver your best final answer based on already verified outputs."
            )
        else:
            lines.append("ACTION: Proceed to next step.")

        lines.append("==========================================")
        prompt_text = "\n".join(lines)

        return RecoveryPromptPayload(
            action=action,
            failed_tool=tool_name,
            diagnosis_category=diagnosis.category.value,
            root_cause=diagnosis.root_cause,
            persistence=diagnosis.persistence.value,
            is_blacklisted=is_blacklisted,
            blacklisted_tools=blacklist_list,
            suggested_substitute=suggested_tool,
            remaining_recovery_budget=remaining_budget,
            prompt_text=prompt_text
        )
