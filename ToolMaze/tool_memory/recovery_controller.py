
"""
Recovery Controller for Layer 3.

Translates structured diagnosis, tool health, memory, recovery budget,
DAG path selection, and loop detection into concrete recovery directives.
"""

from typing import Dict, Any, List, Optional, Set, Tuple

from diagnosis.taxonomy import (
    StructuredDiagnosis,
    PersistenceType,
    RecoveryDirective,
)

from .registry import ToolHealthRegistry
from .memory import ToolMemory
from .budget import BudgetTracker
from .loop_detector import LoopDetector

try:
    from dag_rerouting.path_selector import DAGPathSelector
except ImportError:
    try:
        from ..dag_rerouting.path_selector import DAGPathSelector
    except ImportError:
        DAGPathSelector = None


class RecoveryController:
    """Coordinates recovery decisions across CARE's recovery layers."""

    def __init__(
        self,
        health_registry: Optional[ToolHealthRegistry] = None,
        memory: Optional[ToolMemory] = None,
        budget_tracker: Optional[BudgetTracker] = None,
        alternative_tools_map: Optional[Dict[str, List[str]]] = None,
        path_selector: Optional[Any] = None,
        loop_detector: Optional[LoopDetector] = None,
    ):
        self.registry = (
            health_registry if health_registry is not None
            else ToolHealthRegistry()
        )
        self.memory = memory if memory is not None else ToolMemory()
        self.budget = budget_tracker if budget_tracker is not None else BudgetTracker()

        # Retained for constructor compatibility.
        # Static alternatives are not used as an unsafe fallback.
        self.alternative_map = alternative_tools_map or {}

        self.path_selector = (
            path_selector if path_selector is not None
            else (DAGPathSelector() if DAGPathSelector is not None else None)
        )
        self.loop_detector = (
            loop_detector if loop_detector is not None else LoopDetector()
        )

    def _response(
        self,
        action: str,
        suggested_tool: Optional[str],
        rationale: str,
        guidance: str,
        loop_warning: Optional[str] = None,
        target_path: Optional[List[str]] = None,
        **extra,
    ) -> Dict[str, Any]:
        """Build a consistent recovery response."""
        result = {
            "action": action,
            "suggested_tool": suggested_tool,
            "target_path": target_path,
            "rationale": rationale,
            "agent_prompt_guidance": guidance,
            "loop_warning": loop_warning,
        }
        result.update(extra)
        return result

    def decide_recovery(
        self,
        diagnosis: StructuredDiagnosis,
        arguments: Dict[str, Any],
        step_num: int,
        task_json: Optional[Dict[str, Any]] = None,
        executed_tools: Optional[List[str]] = None,
        tool_output: Any = None,
        available_outputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Decide whether to continue, retry, reroute, partially complete,
        or abort after a tool execution.

        tool_output:
            Actual tool result, when available. This is stored in memory
            instead of replacing it with the string "success".

        available_outputs:
            Previously collected tool outputs. Passed to the path selector
            so it can check whether candidate dependencies are resolvable.
        """

        tool_name = diagnosis.tool_name
        exec_tools = (
            executed_tools
            if executed_tools is not None
            else self.memory.get_executed_tools()
        )

        # --------------------------------------------------
        # 1. Detect loops
        # --------------------------------------------------

        loop_result = self.loop_detector.record_call(
            tool_name,
            arguments,
            is_valid=diagnosis.is_valid,
        )

        loop_warning = (
            loop_result.warning_message
            if loop_result.is_loop
            else None
        )

        if loop_result.is_loop and loop_result.suggested_action == "abort":
            return self._response(
                action=RecoveryDirective.ABORT.value,
                suggested_tool=None,
                rationale=(
                    f"Cyclic deadlock detected "
                    f"({loop_result.loop_type}). Recovery aborted."
                ),
                guidance=loop_result.warning_message or (
                    "A repeated tool-call cycle was detected. "
                    "Do not repeat the same call."
                ),
                loop_warning=loop_warning,
            )

        # --------------------------------------------------
        # 2. Handle successful execution
        # --------------------------------------------------

        if diagnosis.is_valid and not loop_result.is_loop:
            self.registry.record_success(tool_name)

            self.memory.record_call(
                tool_name,
                arguments,
                output=tool_output if tool_output is not None else "success",
                is_valid=True,
                step_num=step_num,
            )

            self.budget.record_tool_call(
                tool_name,
                is_recovery=False,
            )

            return self._response(
                action=RecoveryDirective.CONTINUE.value,
                suggested_tool=tool_name,
                rationale=(
                    "Tool executed successfully and passed deterministic "
                    "validation."
                ),
                guidance="",
            )

        # --------------------------------------------------
        # 3. Record failure exactly once
        # --------------------------------------------------

        is_permanent = (
            diagnosis.persistence == PersistenceType.PERMANENT
            or loop_result.is_loop
        )

        failure_category = (
            "loop_deadlock"
            if loop_result.is_loop
            else diagnosis.category.value
        )

        self.registry.record_failure(
            tool_name,
            category=failure_category,
            is_permanent=is_permanent,
        )

        self.memory.record_call(
            tool_name,
            arguments,
            output=diagnosis.raw_error,
            is_valid=False,
            step_num=step_num,
        )

        self.budget.record_tool_call(
            tool_name,
            is_recovery=True,
        )

        # --------------------------------------------------
        # 4. Check recovery budget
        # --------------------------------------------------

        if not self.budget.has_recovery_budget():
            partial_progress = self.budget.get_partial_progress()

            if partial_progress > 0.0:
                return self._response(
                    action="partial_completion",
                    suggested_tool=None,
                    rationale=(
                        "Recovery budget exhausted after completing "
                        f"{partial_progress:.0%} of task steps."
                    ),
                    guidance=(
                        "Recovery budget exhausted. Do not make further "
                        "tool calls. Produce the best possible answer using "
                        "only verified outputs already collected."
                    ),
                    loop_warning=loop_warning,
                    partial_progress=partial_progress,
                )

            return self._response(
                action=RecoveryDirective.ABORT.value,
                suggested_tool=None,
                rationale="Recovery budget exhausted.",
                guidance=(
                    "Do not attempt further tool calls. "
                    "Produce the best possible answer using verified results."
                ),
                loop_warning=loop_warning,
            )

        # --------------------------------------------------
        # 5. Handle blacklisted tools
        # --------------------------------------------------

        if self.registry.is_blacklisted(tool_name):
            alt_tool, alt_reason, target_path = (
                self._find_healthy_alternative(
                    tool_name,
                    task_json,
                    exec_tools,
                    available_outputs,
                )
            )

            if alt_tool:
                record = self.registry.get_record(tool_name)
                blacklist_reason = (
                    record.blacklist_reason if record else "blacklisted"
                )

                return self._response(
                    action=RecoveryDirective.REROUTE.value,
                    suggested_tool=alt_tool,
                    target_path=target_path,
                    rationale=(
                        f"Tool '{tool_name}' is blacklisted "
                        f"({blacklist_reason}). {alt_reason}"
                    ),
                    guidance=(
                        f"Do not call '{tool_name}' again. "
                        f"Follow the selected alternative path beginning "
                        f"with '{alt_tool}'."
                    ),
                    loop_warning=loop_warning,
                )

            return self._response(
                action=RecoveryDirective.ABORT.value,
                suggested_tool=None,
                rationale=(
                    f"Tool '{tool_name}' is blacklisted and no viable "
                    "alternative DAG path was found."
                ),
                guidance=(
                    "Do not call the failed tool again. "
                    "Use verified results already collected and "
                    "provide a graceful fallback."
                ),
                loop_warning=loop_warning,
            )

        # --------------------------------------------------
        # 6. Handle transient failures
        # --------------------------------------------------

        if (
            diagnosis.persistence == PersistenceType.TRANSIENT
            and not loop_result.is_loop
        ):
            if self.budget.can_retry_tool(tool_name):
                return self._response(
                    action=RecoveryDirective.RETRY.value,
                    suggested_tool=tool_name,
                    rationale=(
                        f"Transient failure detected on '{tool_name}'. "
                        "Retry budget is available."
                    ),
                    guidance=(
                        f"Retry '{tool_name}' with verified parameters. "
                        "Avoid repeating any incorrect arguments."
                    ),
                    loop_warning=loop_warning,
                )

            # Retry budget exhausted: try a DAG-aware alternative.
            alt_tool, alt_reason, target_path = (
                self._find_healthy_alternative(
                    tool_name,
                    task_json,
                    exec_tools,
                    available_outputs,
                )
            )

            if alt_tool:
                return self._response(
                    action=RecoveryDirective.REROUTE.value,
                    suggested_tool=alt_tool,
                    target_path=target_path,
                    rationale=(
                        f"Retry budget for '{tool_name}' is exhausted. "
                        f"{alt_reason}"
                    ),
                    guidance=(
                        f"Stop retrying '{tool_name}'. "
                        f"Follow the selected alternative path beginning "
                        f"with '{alt_tool}'."
                    ),
                    loop_warning=loop_warning,
                )

            return self._response(
                action=RecoveryDirective.ABORT.value,
                suggested_tool=None,
                rationale=(
                    f"Retry budget for '{tool_name}' is exhausted and "
                    "no viable alternative path was found."
                ),
                guidance=(
                    "Do not retry the failed tool. "
                    "Return the best possible result from verified outputs."
                ),
                loop_warning=loop_warning,
            )

        # --------------------------------------------------
        # 7. Default: try DAG-aware rerouting
        # --------------------------------------------------

        alt_tool, alt_reason, target_path = (
            self._find_healthy_alternative(
                tool_name,
                task_json,
                exec_tools,
                available_outputs,
            )
        )

        if alt_tool:
            return self._response(
                action=RecoveryDirective.REROUTE.value,
                suggested_tool=alt_tool,
                target_path=target_path,
                rationale=(
                    f"Rerouting from '{tool_name}'. {alt_reason}"
                ),
                guidance=(
                    f"Do not continue using '{tool_name}'. "
                    f"Follow the selected alternative path beginning "
                    f"with '{alt_tool}'."
                ),
                loop_warning=loop_warning,
            )

        return self._response(
            action=RecoveryDirective.ABORT.value,
            suggested_tool=None,
            rationale="No viable recovery path was identified.",
            guidance=(
                "No safe alternative path is available. "
                "Stop recovery and use verified results for a graceful fallback."
            ),
            loop_warning=loop_warning,
        )

    def _find_healthy_alternative(
        self,
        tool_name: str,
        task_json: Optional[Dict[str, Any]] = None,
        executed_tools: Optional[List[str]] = None,
        available_outputs: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[str], str, Optional[List[str]]]:
        """
        Find a viable alternative using DAGPathSelector.

        Use the legacy alternative map only when no declared solution
        paths are available. Never use arbitrary DAG nodes as substitutes.
        """

        blacklisted: Set[str] = set(
            self.registry.get_blacklisted_tools()
        )

        exec_tools = (
            executed_tools
            if executed_tools is not None
            else self.memory.get_executed_tools()
        )

        # A declared path must be evaluated by the DAG-aware selector.
        has_declared_paths = bool(
            task_json
            and (
                task_json.get("valid_paths")
                or task_json.get("valid_solution_paths")
                or task_json.get("alternative_paths")
            )
        )

        if has_declared_paths:
            if self.path_selector is None:
                return None, "DAG path selector is unavailable.", None

            candidate = self.path_selector.find_reroute(
                failed_tool=tool_name,
                task_json=task_json,
                blacklisted_tools=blacklisted,
                executed_tools=exec_tools,
                available_outputs=available_outputs,
            )

            if candidate is None or not getattr(
                candidate, "is_viable", False
            ):
                reason = getattr(
                    candidate,
                    "reason",
                    "No viable alternative path found.",
                )
                return None, reason, None

            selected_tool = getattr(candidate, "selected_tool", None)

            if not selected_tool:
                return None, "Candidate did not specify a replacement tool.", None

            if selected_tool in blacklisted:
                return None, "Selected replacement is blacklisted.", None

            return (
                selected_tool,
                getattr(candidate, "reason", "DAG alternative selected."),
                getattr(candidate, "target_path", None),
            )

        # Backward-compatible behavior for callers that provide no
        # declared solution paths or task DAG.
        for alternative in self.alternative_map.get(tool_name, []):
            if alternative == tool_name:
                continue

            if alternative in blacklisted:
                continue

            return (
                alternative,
                "Selected a configured legacy alternative because "
                "no declared solution paths were provided.",
                None,
            )

        return None, "No viable alternative was found.", None

    def reset(self):
        """Reset all recovery state."""
        self.registry.reset()
        self.memory.reset()
        self.budget.reset()
        self.loop_detector.reset()
