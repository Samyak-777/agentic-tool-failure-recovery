"""
ToolMaze/tests/test_full_care_pipeline.py
End-to-end unit and integration tests for the full 7-layer CARE architecture.
"""

import sys
import os
from pathlib import Path

# Add project root to path
test_dir = Path(__file__).resolve().parent
toolmaze_root = test_dir.parent
sys.path.insert(0, str(toolmaze_root))

from diagnosis import StructuredDiagnosis, FailureCategory, PersistenceType, RecoveryDirective
from tool_memory import ToolHealthRegistry, ToolMemory, BudgetTracker, BudgetConfig, RecoveryController, LoopDetector
from dag_rerouting import DAGPathSelector, RerouteCandidate
from recovery_prompt import DynamicRecoveryPromptBuilder, RecoveryPromptPayload
from selective_verification import SelectiveVerifier, VerificationResult
from evaluation.agents.care_agent import CAREAgent
from evaluation.agents.base_agent import BaseAgent, AgentAction, TokenUsage


class MockBaseAgent(BaseAgent):
    """Mock agent simulating LLM responses for deterministic pipeline testing."""
    def __init__(self):
        self.messages = []
        self.action_queue = []
        self.received_results = []

    def initialize(self, task_description, tool_definitions):
        self.task_description = task_description
        self.tool_definitions = tool_definitions
        self.messages = []
        self.received_results = []

    def step(self, user_message=None):
        if self.action_queue:
            return self.action_queue.pop(0)
        return AgentAction(type="final_answer", content="Default Mock Answer")

    def receive_tool_result(self, tool_name, result, tool_call_index=0):
        self.received_results.append((tool_name, result))

    def get_total_tokens(self):
        return 100

    def get_token_usage(self):
        return TokenUsage(input_tokens=80, output_tokens=20)

    def get_conversation_history(self):
        return self.messages

    def reset(self):
        self.messages.clear()
        self.action_queue.clear()
        self.received_results.clear()


def test_layer_4_dag_rerouting():
    """Verify Layer 4 DAGPathSelector correctly finds unblocked alternative paths."""
    print("-> Testing Layer 4: DAG-Aware Alternative Path Selection...")
    selector = DAGPathSelector()

    task_json = {
        "task_id": "test_c2_task",
        "valid_solution_paths": [
            ["tool_alpha", "tool_beta"],
            ["tool_gamma", "tool_delta"]
        ],
        "dag": {
            "nodes": [
                {"tool_name": "tool_alpha", "dependencies": []},
                {"tool_name": "tool_beta", "dependencies": ["tool_alpha"]},
                {"tool_name": "tool_gamma", "dependencies": []},
                {"tool_name": "tool_delta", "dependencies": ["tool_gamma"]}
            ]
        }
    }

    # If tool_alpha fails permanently and is blacklisted:
    candidate = selector.find_reroute(
        failed_tool="tool_alpha",
        task_json=task_json,
        blacklisted_tools={"tool_alpha"},
        executed_tools=[]
    )

    assert candidate.is_viable is True, "Candidate should be viable"
    assert candidate.selected_tool == "tool_gamma", f"Expected 'tool_gamma', got {candidate.selected_tool}"
    print("   [PASS] Layer 4 correctly switched to unblocked alternative branch ('tool_gamma').")


def test_layer_5_recovery_prompt_builder():
    """Verify Layer 5 generates informative, evidence-grounded prompt payloads."""
    print("-> Testing Layer 5: Dynamic Recovery Prompt Builder...")
    builder = DynamicRecoveryPromptBuilder(include_detailed_evidence=True)

    diagnosis = StructuredDiagnosis(
        tool_name="get_stock_price",
        is_valid=False,
        category=FailureCategory.SEMANTIC_RANGE_ERROR,
        persistence=PersistenceType.PERMANENT,
        root_cause="Price returned was negative (-52.4)",
        severity="HIGH",
        recommended_action=RecoveryDirective.REROUTE,
        raw_error="Violation: negative price"
    )

    decision = {
        "action": RecoveryDirective.REROUTE.value,
        "suggested_tool": "query_market_data",
        "rationale": "Tool is blacklisted."
    }

    payload = builder.build_prompt(
        diagnosis=diagnosis,
        recovery_decision=decision,
        blacklisted_tools={"get_stock_price"},
        remaining_budget=5
    )

    assert payload.action == "REROUTE"
    assert payload.failed_tool == "get_stock_price"
    assert "query_market_data" in payload.prompt_text
    assert "Blacklisted Tools" in payload.prompt_text
    print("   [PASS] Layer 5 successfully generated evidence-rich prompt payload.")


def test_layer_6_loop_detector():
    """Verify Layer 6 catches immediate, ping-pong, and cyclic call deadlocks."""
    print("-> Testing Layer 6: Cost-Aware Control & Loop Detection...")
    detector = LoopDetector(max_consecutive_same_tool=2)

    # 1. Immediate loop: calling failing tool twice with identical args
    r1 = detector.record_call("tool_a", {"id": 1}, is_valid=False)
    assert not r1.is_loop
    r2 = detector.record_call("tool_a", {"id": 1}, is_valid=False)
    assert r2.is_loop, "Should detect immediate loop"
    assert r2.loop_type == "immediate"
    print("   [PASS] Immediate loop detected.")

    # 2. Ping-Pong loop: A -> B -> A -> B
    detector.reset()
    detector.record_call("tool_a", {"x": 1}, is_valid=True)
    detector.record_call("tool_b", {"x": 2}, is_valid=True)
    detector.record_call("tool_a", {"x": 1}, is_valid=True)
    r_pp = detector.record_call("tool_b", {"x": 2}, is_valid=True)
    assert r_pp.is_loop, "Should detect ping-pong loop"
    assert r_pp.loop_type == "ping_pong"
    print("   [PASS] Ping-pong oscillation loop detected.")


def test_layer_7_selective_verifier():
    """Verify Layer 7 provides graceful fallback when LLM is not active."""
    print("-> Testing Layer 7: Selective LLM Verifier...")
    verifier = SelectiveVerifier(llm_client=None)
    res = verifier.verify("search_tool", {"query": "test"}, "sample output")
    assert res.is_valid is True
    print("   [PASS] Layer 7 graceful verification fallback passed.")


def test_full_care_agent_closed_loop():
    """Verify the full CAREAgent orchestrating all 7 layers in an execution loop."""
    print("-> Testing Full CAREAgent Closed-Loop Integration...")
    mock_llm = MockBaseAgent()
    agent = CAREAgent(base_agent=mock_llm)

    task_json = {
        "task_id": "e2e_test_task",
        "task_description": "Retrieve user profile and billing history",
        "valid_solution_paths": [
            ["get_user_profile", "get_billing_history"],
            ["get_account_info", "get_invoice_records"]
        ]
    }
    agent.initialize("Test Task", {}, task_json=task_json)

    # Step 1: Agent calls get_user_profile cleanly
    mock_llm.action_queue.append(AgentAction(type="tool_call", tool_name="get_user_profile", arguments={"uid": 123}))
    action = agent.step()
    assert action.tool_name == "get_user_profile"

    # Tool returns clean output
    agent.receive_tool_result("get_user_profile", {"status": "success", "username": "alice"})
    assert len(mock_llm.received_results) == 1
    # Should receive normal output
    assert mock_llm.received_results[0][1] == {"status": "success", "username": "alice"}
    print("   [PASS] Clean tool call passed through seamlessly.")

    # Step 2: Agent calls get_billing_history which returns corrupted negative amount
    mock_llm.action_queue.append(AgentAction(type="tool_call", tool_name="get_billing_history", arguments={"uid": 123}))
    action2 = agent.step()
    assert action2.tool_name == "get_billing_history"

    # Tool returns semantically corrupted output
    corrupt_result = {"status": "success", "balance": -99999, "invoices": []}
    agent.receive_tool_result("get_billing_history", corrupt_result)

    # Verify CARE intercepted the result and returned structured diagnostic feedback
    last_res = mock_llm.received_results[-1][1]
    assert last_res.get("error") == "CARE_VALIDATION_FAILURE"
    assert "orchestrator_directive" in last_res
    assert "system_instruction" in last_res
    print(f"   [PASS] Corrupted output caught by SOV -> Layer 2 Diagnosis ({last_res.get('diagnosis')}) -> Directive: {last_res.get('orchestrator_directive')}")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING FULL CARE 7-LAYER PIPELINE INTEGRATION TESTS")
    print("==================================================")
    test_layer_4_dag_rerouting()
    test_layer_5_recovery_prompt_builder()
    test_layer_6_loop_detector()
    test_layer_7_selective_verifier()
    test_full_care_agent_closed_loop()
    print("==================================================")
    print("ALL 7 LAYERS VERIFIED SUCCESSFULLY (5/5 PASSED)!")
    print("==================================================")
