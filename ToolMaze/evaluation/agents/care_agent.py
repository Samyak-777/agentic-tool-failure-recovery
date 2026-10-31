"""
ToolMaze/evaluation/agents/care_agent.py
Cost-Aware Recovery Engine (CARE) Agent

Orchestrates all 7 layers of resilience:
- Layer 1: Deterministic Semantic Output Validation (SOV)
- Layer 2: Structured Failure Diagnosis
- Layer 3: Failure-State Tracking & Tool Memory
- Layer 4: DAG-Aware Alternative Path Selection
- Layer 5: Dynamic Recovery Prompts with Evidence
- Layer 6: Cost-Aware Control & Loop Detection
- Layer 7: Selective LLM Verification
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Set

from .base_agent import BaseAgent, AgentAction, TokenUsage, ToolCall

try:
    from .openai_agent import OpenAIAgent
except ImportError:
    OpenAIAgent = None

# Import CARE Layers
try:
    from semantic_validation import (
        SemanticValidationPipeline,
        ValidationConfig,
        PipelineStatus,
        CheckerStatus
    )
except ImportError:
    SemanticValidationPipeline = None
    ValidationConfig = None
    PipelineStatus = None
    CheckerStatus = None

from diagnosis import (
    StructuredDiagnosisEngine,
    StructuredDiagnosis,
    FailureCategory,
    PersistenceType,
    RecoveryDirective
)
from tool_memory import (
    ToolHealthRegistry,
    ToolMemory,
    BudgetTracker,
    BudgetConfig,
    RecoveryController,
    LoopDetector
)
from dag_rerouting import DAGPathSelector, RerouteCandidate
from recovery_prompt import DynamicRecoveryPromptBuilder, RecoveryPromptPayload
from selective_verification import SelectiveVerifier

logger = logging.getLogger(__name__)


class CAREAgent(BaseAgent):
    """CARE Agent wrapping underlying LLM with 7-layer resilience orchestration."""

    def __init__(
        self,
        base_agent: Optional[BaseAgent] = None,
        model: str = "gemma-4-31b-it",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        budget_config: Optional[BudgetConfig] = None,
        enable_sov: bool = True,
        enable_care_recovery: bool = True,
        sov: Optional[Any] = None,
        tools_dir: Optional[str] = None,
        telemetry_recorder: Optional[Any] = None
    ):
        self.telemetry_recorder = telemetry_recorder
        # 1. Base Agent (Delegate LLM)
        if base_agent:
            self.base_agent = base_agent
        elif OpenAIAgent is not None:
            self.base_agent = OpenAIAgent(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            raise ImportError("OpenAIAgent requires the 'openai' package to be installed.")

        self.enable_sov = enable_sov
        self.enable_care_recovery = enable_care_recovery
        self.execution_id = str(uuid.uuid4())

        # 2. Layer 1: Semantic Output Validation Pipeline
        if sov is not None:
            self.sov = sov
        elif SemanticValidationPipeline is not None:
            try:
                from tools.loader import ToolLoader
                t_dir = Path(tools_dir) if tools_dir else Path(__file__).resolve().parent.parent.parent / "tools"
                def_dir = t_dir / "definitions"
                if def_dir.exists():
                    loader = ToolLoader(str(def_dir))
                    self.sov = SemanticValidationPipeline(ValidationConfig(), loader)
                else:
                    self.sov = None
            except Exception as e:
                logger.debug(f"Could not initialize default SVL: {e}")
                self.sov = None
        else:
            self.sov = None

        # 3. Layer 2: Structured Diagnosis Engine
        self.diagnosis_engine = StructuredDiagnosisEngine()

        # 4. Layer 4: DAG Path Selector
        self.path_selector = DAGPathSelector()

        # 5. Layer 6: Loop Detector
        self.loop_detector = LoopDetector()

        # 6. Layer 3: Tool Health, Memory, Budget & Recovery Controller
        self.health_registry = ToolHealthRegistry()
        self.tool_memory = ToolMemory()
        self.budget_tracker = BudgetTracker(config=budget_config or BudgetConfig(max_recovery_attempts=5, max_retries_per_tool=1))
        self.recovery_controller = RecoveryController(
            health_registry=self.health_registry,
            memory=self.tool_memory,
            budget_tracker=self.budget_tracker,
            path_selector=self.path_selector,
            loop_detector=self.loop_detector
        )

        # 7. Layer 5: Dynamic Recovery Prompt Builder
        self.prompt_builder = DynamicRecoveryPromptBuilder(include_detailed_evidence=True)

        # 8. Layer 7: Selective Verifier
        self.selective_verifier = SelectiveVerifier(
            llm_client=getattr(self.base_agent, "client", None),
            model=model
        )

        # Session State
        self.task_json: Dict[str, Any] = {}
        self.tool_definitions: Dict[str, Any] = {}
        self.step_counter: int = 0
        self.last_action: Optional[AgentAction] = None
        self.last_recovery_directive: Optional[str] = None
        self.recovery_prompts_injected: int = 0
        self.force_abort: bool = False
        # DAG-enforced execution state.
        self.active_path: Optional[List[str]] = None
        self.active_path_index: int = 0

        # Successful execution state. These must not be populated by failed calls.
        self.completed_tools: Set[str] = set()
        self.completed_outputs: Dict[str, Any] = {}

        # Associate a dispatched invocation with the DAG step it represents.
        self.last_dispatched_tool: Optional[str] = None
        self.last_dispatched_node_index: Optional[int] = None

        # Preserve the existing recovery decision; do not introduce a new retry counter.
        self.pending_retry_tool: Optional[str] = None

    def initialize(self, task_description: str, tool_definitions: Dict[str, Any], task_json: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the CARE Agent with task definitions."""
        self.task_json = task_json or {}
        self.tool_definitions = tool_definitions
        self.execution_id = str(uuid.uuid4())
        task_id = self.task_json.get("task_id", "task_care")
        if self.sov is not None:
            try:
                self.sov.create_execution_state(self.execution_id, task_id)
            except Exception:
                pass

        self.step_counter = 0
        self.last_action = None
        self.last_recovery_directive = None
        self.recovery_prompts_injected = 0
        self.force_abort = False
        

        # Fix #12: Apply topology-aware budget
        topology = self.task_json.get("topology", "c1") or "c1"
        try:
            from tool_memory.budget import get_topology_budget
            topo_budget = get_topology_budget(topology)
            self.budget_tracker.config = topo_budget
        except Exception:
            pass

        # Fix #13: Wire task DAG step count into budget tracker for PRP
        dag = self.task_json.get("dag", {})
        dag_nodes = dag.get("nodes", []) if isinstance(dag, dict) else []
        expected_steps = len(dag_nodes) if dag_nodes else 0

        self.health_registry.reset()
        self.tool_memory.reset()
        self.budget_tracker.reset()
        self.loop_detector.reset()
        self.recovery_controller.reset()
        self.active_path = None
        self.active_path_index = 0
        self.completed_tools.clear()
        self.completed_outputs.clear()
        self.last_dispatched_tool = None
        self.last_dispatched_node_index = None
        self.pending_retry_tool = None
        # Restore after reset
        if expected_steps:
            self.budget_tracker.set_total_steps(expected_steps)

        self._initialize_active_path()
        self.base_agent.initialize(task_description, tool_definitions)

    def set_telemetry_recorder(self, recorder: Optional[Any]) -> None:
        """Set task telemetry recorder."""
        self.telemetry_recorder = recorder

    def set_task_json(self, task_json: Dict[str, Any]) -> None:
        """Set task specification for DAG-aware and recovery routing."""
        self.task_json = task_json or {}

    def _find_tool_definition(self, tool_name: str) -> Optional[Dict[str, Any]]:
        if not self.tool_definitions:
            return None
        if isinstance(self.tool_definitions, list):
            for t in self.tool_definitions:
                if t.get("name") == tool_name:
                    return t
                if t.get("function", {}).get("name") == tool_name:
                    return t.get("function")
        elif isinstance(self.tool_definitions, dict):
            if "function_call" in self.tool_definitions:
                for t in self.tool_definitions["function_call"]:
                    if t.get("name") == tool_name:
                        return t
                    if t.get("function", {}).get("name") == tool_name:
                        return t.get("function")
            if tool_name in self.tool_definitions:
                return self.tool_definitions[tool_name]
        return None

    def _are_tool_args_compatible(self, tool_name: str, args: Dict[str, Any]) -> bool:
        tool_def = self._find_tool_definition(tool_name)
        if not tool_def:
            return True
        params = tool_def.get("parameters", {})
        required = params.get("required", [])
        if required and not all(r in args for r in required):
            return False
        return True


    def _initialize_active_path(self) -> None:
        """Initialize a permitted task path when one is explicitly available."""
        raw_paths = (
            self.task_json.get("valid_paths")
            or self.task_json.get("valid_solution_paths")
            or []
        )

        if not raw_paths:
            self.active_path = None
            self.active_path_index = 0
            return

        normalized = []

        for path in raw_paths:
            if isinstance(path, dict):
                tools = path.get("tools")
                if not tools and isinstance(path.get("execution_trace"), list):
                    tools = [
                        step.get("tool_name")
                        for step in path["execution_trace"]
                        if isinstance(step, dict) and step.get("tool_name")
                    ]
            elif isinstance(path, (list, tuple)):
                tools = list(path)
            else:
                continue

            if (
                isinstance(tools, list)
                and tools
                and all(isinstance(tool, str) and tool for tool in tools)
            ):
                normalized.append(tools)

        if not normalized:
            self.active_path = None
            self.active_path_index = 0
            return

        self.active_path = normalized[0]
        self.active_path_index = 0
        logger.info(
            "CARE DAG: initialized active path with %d steps",
            len(self.active_path),
        )


    def _expected_tool_for_current_step(self) -> Optional[str]:
        """Return the controller-required next tool, if an active path exists."""
        if not self.active_path:
            return None

        if self.active_path_index < 0:
            return None

        if self.active_path_index >= len(self.active_path):
            return None

        return self.active_path[self.active_path_index]


    def step(self, user_message: Optional[str] = None) -> AgentAction:
        """Execute one reasoning step with proactive loop & abort guards."""
        self.step_counter += 1

        # Early exit if recovery engine aborted
        if self.force_abort:
            logger.info("CARE Guard: Force abort active. Delivering best synthesis.")
            return AgentAction(
                type="final_answer",
                content="[CARE ABORT]: Recovery budget exhausted or all valid paths blocked. Finalizing task with best verified observations."
            )

        # Invoke base agent for next action
        action = self.base_agent.step(user_message=user_message)
        self.last_action = action

        expected_tool = self._expected_tool_for_current_step()

        if expected_tool:
            max_corrections = 3
            corrections = 0

            while corrections < max_corrections:

                # A final answer is also premature if required path steps remain.
                is_wrong_tool = (
                    action.type == "tool_call"
                    and action.tool_name != expected_tool
                )

                is_early_final = action.type == "final_answer"

                if not is_wrong_tool and not is_early_final:
                    break

                if is_wrong_tool:
                    logger.warning(
                        "CARE DAG: rejected proposed tool '%s'; expected '%s'.",
                        action.tool_name,
                        expected_tool,
                    )
                else:
                    logger.warning(
                        "CARE DAG: rejected early final answer; expected '%s'.",
                        expected_tool,
                    )

                corrections += 1

                correction_message = (
                    "IMPORTANT: The task execution controller requires the next "
                    f"tool to be '{expected_tool}'. "
                    "Do not provide a final answer yet. "
                    "Do not call another tool. "
                    f"Produce a tool call for '{expected_tool}' using the "
                    "available task information and verified outputs."
                )

                action = self.base_agent.step(
                    user_message=correction_message
                )
                self.last_action = action

            # Never allow a wrong tool call or early final answer to escape.
            if (
                action.type == "tool_call"
                and action.tool_name != expected_tool
            ) or action.type == "final_answer":

                logger.error(
                    "CARE DAG: unable to obtain required tool '%s' after %d "
                    "correction attempts. Blocking off-path action.",
                    expected_tool,
                    corrections,
                )

                return AgentAction(
                    type="final_answer",
                    content=(
                        "[CARE EXECUTION BLOCKED] The required next tool "
                        f"'{expected_tool}' was not produced. "
                        "The task is incomplete and must not be counted as "
                        "a successful execution."
                    ),
                )        
        # Guard: Check if agent is attempting to call a blacklisted tool
        if action.type == "tool_call" and action.tool_name:
            if self.health_registry.is_blacklisted(action.tool_name):
                logger.warning(f"CARE Guard: Agent attempted to invoke blacklisted tool '{action.tool_name}'. Intercepting.")
                candidate = self.path_selector.find_reroute(
                    failed_tool=action.tool_name,
                    task_json=self.task_json,
                    blacklisted_tools=self.health_registry.get_blacklisted_tools(),
                    executed_tools=self.tool_memory.get_executed_tools()
                )
                if self.telemetry_recorder:
                    try:
                        self.telemetry_recorder.record_dag_path_selection(
                            failed_tool=action.tool_name,
                            candidate_tools=getattr(candidate, "candidate_tools", []),
                            selected_tool=getattr(candidate, "selected_tool", None),
                            is_viable=getattr(candidate, "is_viable", False),
                            reason=getattr(candidate, "reason", "Blacklist guard interception"),
                            target_path=getattr(candidate, "target_path", None)
                        )
                    except Exception:
                        pass
                if candidate.is_viable and candidate.selected_tool:
                    original_tool = action.tool_name
                    replacement_tool = candidate.selected_tool
                    if self._are_tool_args_compatible(replacement_tool, action.arguments or {}):
                        logger.info(
                            f"CARE Reroute: Substituting blacklisted "
                            f"'{original_tool}' with '{replacement_tool}'."
                        )
                        action.tool_name = replacement_tool
                    else:
                        logger.warning(
                            f"CARE Reroute: Candidate '{replacement_tool}' requires arguments "
                            f"not present in '{original_tool}' call. Bypassing silent substitution."
                        )

        return action

    def _basic_result_is_successful(self, result: Any) -> bool:
        """Check explicit execution failure signals when SOV is disabled."""

        if result is None:
            return False

        if isinstance(result, dict):
            if result.get("status") == "error":
                return False

            if result.get("success") is False:
                return False

            if result.get("is_error") is True:
                return False

            if result.get("error"):
                return False

        return True    
    
    def _record_successful_path_step(
        self,
        tool_name: str,
        result: Dict[str, Any],
    ) -> None:
        """Record a successful tool result and advance the active route once."""

        expected_tool = self._expected_tool_for_current_step()

        if expected_tool != tool_name:
            logger.warning(
                "CARE DAG: result for '%s' does not match expected tool '%s'. "
                "Path index unchanged.",
                tool_name,
                expected_tool,
            )
            return

        # Do not advance the same path step twice.
        self.completed_tools.add(tool_name)
        self.completed_outputs[tool_name] = result

        self.active_path_index += 1

        if self.pending_retry_tool == tool_name:
            self.pending_retry_tool = None

        logger.info(
            "CARE DAG: completed '%s'; next path index=%d",
            tool_name,
            self.active_path_index,
        )

    def receive_tool_result(self, tool_name: str, result: Dict[str, Any], tool_call_index: int = 0) -> None:
        """Process tool results through the 7-layer validation and recovery pipeline."""
        if not self.enable_sov:
            if self._basic_result_is_successful(result):
                self._record_successful_path_step(tool_name, result)
            else:
                logger.warning(
                    "CARE DAG: SOV disabled, but result for '%s' contains "
                    "an explicit execution failure. Path index unchanged.",
                    tool_name,
                )

                # Do not mark the node complete.
                # Preserve the existing SOV-disabled behavior: forward the result
                # without invoking a new diagnosis/retry policy here.

            self.base_agent.receive_tool_result(
                tool_name,
                result,
                tool_call_index
            )
            return

        tool_args = (self.last_action.arguments if self.last_action and self.last_action.tool_name == tool_name else {})
        query = self.task_json.get("task_description", "")

        # ----------------------------------------------------
        # Layer 1: Deterministic Semantic Output Validation
        # ----------------------------------------------------
        is_clean = True
        val_res_dict = None

        if self.sov is not None and PipelineStatus is not None:
            try:
                val_result = self.sov.validate(
                    tool_name=tool_name,
                    arguments=tool_args,
                    result=result,
                    execution_id=self.execution_id,
                    task_id=self.task_json.get("task_id", "task_0"),
                    step=self.step_counter
                )
                val_res_dict = val_result.to_dict()
                if val_result.pipeline_status in (PipelineStatus.INVALID, PipelineStatus.ERROR):
                    # Tiered SOV: Check if failure is purely non-critical metadata omission
                    failed_checks = getattr(val_result, "failed_checks", {}) or {}
                    failed_keys = set(failed_checks.keys())
                    NON_CRITICAL_METADATA_FIELDS = {
                        "timestamp", "document_timestamp", "created_at", "updated_at",
                        "datetime", "time", "date", "status_code", "execution_time", "elapsed_time"
                    }
                    if failed_keys == {"required"}:
                        req_check = val_result.checks.get("required")
                        details = getattr(req_check, "details", {}) or {}
                        missing = set(details.get("missing_fields", []))
                        null_f = set(details.get("null_fields", []))
                        if (missing | null_f) and (missing | null_f).issubset(NON_CRITICAL_METADATA_FIELDS):
                            logger.info(f"SOV Soft Advisory: Tool '{tool_name}' omitted non-critical metadata {missing | null_f}. Treating output as clean.")
                            is_clean = True
                        else:
                            is_clean = False
                    else:
                        is_clean = False
            except Exception as e:
                logger.debug(f"SVL validation error: {e}")

        # Semantic corruption checks on payload (e.g. negative balances, errors)
        if isinstance(result, dict):
            if result.get("status") == "error" or "error" in result:
                is_clean = False
            for k, v in result.items():
                if any(term in k.lower() for term in ["balance", "price", "count", "age", "qty"]):
                    if isinstance(v, (int, float)) and v < 0:
                        is_clean = False

        

        # If clean, record success and return unmodified output
        if is_clean:
            self.recovery_controller.decide_recovery(
                diagnosis=StructuredDiagnosis(
                    tool_name=tool_name,
                    is_valid=True,
                    category=FailureCategory.SYNTAX_SCHEMA_ERROR,
                    persistence=PersistenceType.TRANSIENT,
                    root_cause="Clean execution",
                    severity="LOW",
                    recommended_action=RecoveryDirective.CONTINUE
                ),
                arguments=tool_args,
                step_num=self.step_counter,
                task_json=self.task_json
            )
            self.budget_tracker.record_step_completed()  # Fix #13: PRP tracking

            self._record_successful_path_step(tool_name, result)
           
            self.base_agent.receive_tool_result(tool_name, result, tool_call_index)
            return

        # ----------------------------------------------------
        # Layer 2: Structured Failure Diagnosis
        # ----------------------------------------------------
        diagnosis = self.diagnosis_engine.diagnose(
            tool_name=tool_name,
            arguments=tool_args,
            raw_result=result,
            validation_result=val_res_dict,
            tool_call_history=self.tool_memory.call_log,
            step_num=self.step_counter
        )

        if self.telemetry_recorder:
            try:
                cat_val = diagnosis.category.value if hasattr(diagnosis.category, "value") else str(diagnosis.category)
                pers_val = diagnosis.persistence.value if hasattr(diagnosis.persistence, "value") else str(diagnosis.persistence)
                act_val = diagnosis.recommended_action.value if hasattr(diagnosis.recommended_action, "value") else str(diagnosis.recommended_action)
                self.telemetry_recorder.record_diagnosis(
                    tool_name=tool_name,
                    category=cat_val,
                    persistence=pers_val,
                    root_cause=diagnosis.root_cause,
                    severity=diagnosis.severity,
                    recommended_action=act_val,
                    evidence={"validation": val_res_dict, "raw_error": diagnosis.raw_error}
                )
            except Exception:
                pass

        # ----------------------------------------------------
        # Layer 7: Selective LLM Verification (if ambiguous)
        # ----------------------------------------------------
        if diagnosis.recommended_action == RecoveryDirective.VERIFY:
            verif = self.selective_verifier.verify(
                tool_name=tool_name,
                arguments=tool_args,
                output=result,
                task_query=query
            )

            if verif.is_valid:
                logger.info(
                    "Layer 7: Borderline output for '%s' verified valid by LLM.",
                    tool_name,
                )

                # Verification has accepted this result, so it can count as
                # successful progress on the active DAG path.
                self._record_successful_path_step(tool_name, result)

                self.base_agent.receive_tool_result(
                    tool_name,
                    result,
                    tool_call_index
                )
                return

        # ----------------------------------------------------
        # Layer 3 & 4 & 6: Recovery Controller Decision
        # ----------------------------------------------------
        recovery_decision = self.recovery_controller.decide_recovery(
            diagnosis=diagnosis,
            arguments=tool_args,
            step_num=self.step_counter,
            task_json=self.task_json,
            executed_tools=self.tool_memory.get_executed_tools()
        )
        self.last_recovery_directive = recovery_decision.get("action")
        
        action_name = recovery_decision.get("action")

        if action_name == "retry":
            self.pending_retry_tool = tool_name

        elif action_name == "reroute":
            target_path = recovery_decision.get("target_path")

            if isinstance(target_path, list) and target_path:
                # The selector has already selected a permitted alternate path.
                self.active_path = target_path
                self.active_path_index = 0

                # Reuse only the consecutive completed prefix.
                while self.active_path_index < len(self.active_path):
                    next_tool = self.active_path[self.active_path_index]

                    if next_tool not in self.completed_tools:
                        break

                    self.active_path_index += 1

                self.pending_retry_tool = None

                logger.info(
                    "CARE DAG: committed alternate path. "
                    "Next tool=%s, path index=%d",
                    self._expected_tool_for_current_step(),
                    self.active_path_index,
                )

            else:
                logger.error(
                    "CARE DAG: reroute selected without a valid target path."
                )
                self.force_abort = True


        if self.telemetry_recorder:
            try:
                self.telemetry_recorder.record_recovery_attempt(
                    failed_tool=tool_name,
                    action=recovery_decision.get("action", "unknown"),
                    suggested_tool=recovery_decision.get("suggested_tool"),
                    remaining_budget=self.budget_tracker.get_remaining_recovery_calls(),
                    loop_warning=recovery_decision.get("loop_warning"),
                    rationale=recovery_decision.get("rationale", "")
                )
                if recovery_decision.get("target_path") or recovery_decision.get("suggested_tool"):
                    self.telemetry_recorder.record_dag_path_selection(
                        failed_tool=tool_name,
                        candidate_tools=[recovery_decision.get("suggested_tool")] if recovery_decision.get("suggested_tool") else [],
                        selected_tool=recovery_decision.get("suggested_tool"),
                        is_viable=bool(recovery_decision.get("suggested_tool")),
                        reason=recovery_decision.get("rationale", ""),
                        target_path=recovery_decision.get("target_path")
                    )
            except Exception:
                pass

        if recovery_decision.get("action") in (RecoveryDirective.ABORT.value, "partial_completion"):
            # Fix #9: treat PARTIAL_COMPLETION as soft abort — stop calling tools
            # but let agent produce a best-effort answer from existing outputs
            self.force_abort = True

        # ----------------------------------------------------
        # Layer 5: Dynamic Recovery Prompt Synthesis
        # ----------------------------------------------------
        recovery_payload = self.prompt_builder.build_prompt(
            diagnosis=diagnosis,
            recovery_decision=recovery_decision,
            blacklisted_tools=self.health_registry.get_blacklisted_tools(),
            remaining_budget=self.budget_tracker.get_remaining_recovery_calls(),
            loop_warning=recovery_decision.get("loop_warning")
        )
        self.recovery_prompts_injected += 1

        # Deliver formatted diagnostic feedback instead of raw corrupted data
        transformed_result = {
            "error": "CARE_VALIDATION_FAILURE",
            "orchestrator_directive": recovery_payload.action,
            "diagnosis": diagnosis.category.value,
            "root_cause": diagnosis.root_cause,
            "system_instruction": recovery_payload.prompt_text
        }

        self.base_agent.receive_tool_result(tool_name, transformed_result, tool_call_index)

    def get_total_tokens(self) -> int:
        return self.base_agent.get_total_tokens()

    def get_token_usage(self) -> TokenUsage:
        return self.base_agent.get_token_usage()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        return self.base_agent.get_conversation_history()

    def reset(self) -> None:
        self.health_registry.reset()
        self.tool_memory.reset()
        self.budget_tracker.reset()
        self.loop_detector.reset()
        self.recovery_controller.reset()
        self.base_agent.reset()
        self.step_counter = 0
        self.force_abort = False
        self.last_action = None
        self.last_recovery_directive = None
        self.active_path = None
        self.active_path_index = 0
        self.completed_tools.clear()
        self.completed_outputs.clear()
        self.last_dispatched_tool = None
        self.last_dispatched_node_index = None
        self.pending_retry_tool = None
