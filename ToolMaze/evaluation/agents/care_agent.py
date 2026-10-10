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
from typing import Dict, Any, Optional, List, Set

from .base_agent import BaseAgent, AgentAction, TokenUsage, ToolCall

try:
    from .openai_agent import OpenAIAgent
except ImportError:
    OpenAIAgent = None

# Import CARE Layers
from semantic_validation import SemanticValidationPipeline
from diagnosis import StructuredDiagnosisEngine, StructuredDiagnosis, FailureCategory, PersistenceType, RecoveryDirective
from tool_memory import ToolHealthRegistry, ToolMemory, BudgetTracker, BudgetConfig, RecoveryController, LoopDetector
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
        enable_care_recovery: bool = True
    ):
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

        # 2. Layer 1: Semantic Output Validation Pipeline
        self.sov = SemanticValidationPipeline()

        # 3. Layer 2: Structured Diagnosis Engine
        self.diagnosis_engine = StructuredDiagnosisEngine()

        # 4. Layer 4: DAG Path Selector
        self.path_selector = DAGPathSelector()

        # 5. Layer 6: Loop Detector
        self.loop_detector = LoopDetector()

        # 6. Layer 3: Tool Health, Memory, Budget & Recovery Controller
        self.health_registry = ToolHealthRegistry()
        self.tool_memory = ToolMemory()
        self.budget_tracker = BudgetTracker(config=budget_config or BudgetConfig(max_recovery_tool_calls=6, max_retries_per_tool=1))
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
        self.step_counter: int = 0
        self.last_action: Optional[AgentAction] = None
        self.last_recovery_directive: Optional[str] = None
        self.recovery_prompts_injected: int = 0
        self.force_abort: bool = False

    def initialize(self, task_description: str, tool_definitions: Dict[str, Any], task_json: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the CARE Agent with task definitions."""
        self.task_json = task_json or {}
        self.step_counter = 0
        self.last_action = None
        self.last_recovery_directive = None
        self.recovery_prompts_injected = 0
        self.force_abort = False

        self.health_registry.reset()
        self.tool_memory.reset()
        self.budget_tracker.reset()
        self.loop_detector.reset()
        self.recovery_controller.reset()

        self.base_agent.initialize(task_description, tool_definitions)

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

        # Guard: Check if agent is attempting to call a blacklisted tool
        if action.type == "tool_call" and action.tool_name:
            if self.health_registry.is_blacklisted(action.tool_name):
                logger.warning(f"CARE Guard: Agent attempted to invoke blacklisted tool '{action.tool_name}'. Intercepting.")
                # Look up alternative immediately
                candidate = self.path_selector.find_reroute(
                    failed_tool=action.tool_name,
                    task_json=self.task_json,
                    blacklisted_tools=self.health_registry.get_blacklisted_tools(),
                    executed_tools=self.tool_memory.get_executed_tools()
                )
                if candidate.is_viable and candidate.selected_tool:
                    logger.info(f"CARE Reroute: Substituting blacklisted '{action.tool_name}' with '{candidate.selected_tool}'.")
                    action.tool_name = candidate.selected_tool

        return action

    def receive_tool_result(self, tool_name: str, result: Dict[str, Any], tool_call_index: int = 0) -> None:
        """Process tool results through the 7-layer validation and recovery pipeline."""
        if not self.enable_sov:
            self.base_agent.receive_tool_result(tool_name, result, tool_call_index)
            return

        tool_args = (self.last_action.arguments if self.last_action and self.last_action.tool_name == tool_name else {})
        query = self.task_json.get("task_description", "")

        # ----------------------------------------------------
        # Layer 1: Deterministic Semantic Output Validation
        # ----------------------------------------------------
        validation_res = self.sov.validate(
            tool_name=tool_name,
            output=result,
            arguments=tool_args,
            task_query=query
        )

        # If clean, record success and return unmodified output
        if validation_res.is_valid and not validation_res.violations:
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
            self.base_agent.receive_tool_result(tool_name, result, tool_call_index)
            return

        # ----------------------------------------------------
        # Layer 2: Structured Failure Diagnosis
        # ----------------------------------------------------
        history = self.tool_memory.get_tool_history(tool_name)
        diagnosis = self.diagnosis_engine.diagnose(
            tool_name=tool_name,
            raw_output=result,
            violations=validation_res.violations,
            arguments=tool_args,
            history=history
        )

        # ----------------------------------------------------
        # Layer 7: Selective LLM Verification (if ambiguous)
        # ----------------------------------------------------
        if validation_res.is_valid and validation_res.violations:
            # Borderline case
            verif = self.selective_verifier.verify(
                tool_name=tool_name,
                arguments=tool_args,
                output=result,
                task_query=query
            )
            if verif.is_valid:
                logger.info(f"Layer 7: Borderline output for '{tool_name}' verified valid by LLM.")
                self.base_agent.receive_tool_result(tool_name, result, tool_call_index)
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

        if recovery_decision.get("action") == RecoveryDirective.ABORT.value:
            self.force_abort = True

        # ----------------------------------------------------
        # Layer 5: Dynamic Recovery Prompt Synthesis
        # ----------------------------------------------------
        recovery_payload = self.prompt_builder.build_prompt(
            diagnosis=diagnosis,
            recovery_decision=recovery_decision,
            blacklisted_tools=self.health_registry.get_blacklisted_tools(),
            remaining_budget=self.budget_tracker.remaining_recovery_calls,
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
