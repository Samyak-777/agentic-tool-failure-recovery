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


def test_layer_4_dag_rerouting_toolmaze_dict_format():
    """Verify Layer 4 handles ToolMaze's native dictionary-format valid_paths and alternative_tools."""
    selector = DAGPathSelector()

    task_json = {
        "task_id": "test_c2_native",
        "valid_paths": [
            {
                "path_id": "path_0",
                "tools": ["get_hotel_info_booking", "get_flight_info", "book_hotel", "send_email"]
            },
            {
                "path_id": "path_1",
                "tools": ["get_hotel_info_booking", "get_flight_info_aviationstack", "book_hotel", "send_email"]
            }
        ],
        "alternative_tools": [
            "get_flight_info",
            "get_flight_info_aviationstack"
        ]
    }

    # Step 1: 'get_hotel_info_booking' already executed. Step 2: 'get_flight_info' failed.
    candidate = selector.find_reroute(
        failed_tool="get_flight_info",
        task_json=task_json,
        blacklisted_tools={"get_flight_info"},
        executed_tools=["get_hotel_info_booking"]
    )

    assert candidate.is_viable is True, "Candidate should be viable"
    assert candidate.selected_tool == "get_flight_info_aviationstack", f"Expected 'get_flight_info_aviationstack', got {candidate.selected_tool}"
    print("   [PASS] Layer 4 correctly rerouted using ToolMaze native valid_paths dict format.")



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


def test_layer_1_tiered_sov_soft_advisory():
    """Verify that omitting non-critical metadata (e.g. timestamp) does NOT trigger fatal error."""
    print("-> Testing Tiered SOV: Non-Critical Metadata Soft Advisory...")
    mock_llm = MockBaseAgent()
    agent = CAREAgent(base_agent=mock_llm)
    agent.initialize("Test Task", {})

    mock_llm.action_queue.append(AgentAction(type="tool_call", tool_name="create_document", arguments={"content": "hello"}))
    agent.step()

    # create_document returns valid data but omits 'timestamp'
    doc_result = {
        "message": "Note saved successfully",
        "note_id": "NOTE18E3D",
        "title": "Untitled",
        "content_length": 5,
        "tags": []
    }
    agent.receive_tool_result("create_document", doc_result)
    assert len(mock_llm.received_results) == 1
    # Must NOT be intercepted as CARE_VALIDATION_FAILURE
    assert mock_llm.received_results[0][1] == doc_result
    assert agent.force_abort is False
    print("   [PASS] Non-critical metadata omission passed through cleanly as soft advisory without abort.")


def test_layer_5_full_workflow_path_injection():
    """Verify Layer 5 injects the full alternative sequence when target_path is available."""
    print("-> Testing Layer 5: Full-Subpath Sequence Injection in Reroute Prompt...")
    builder = DynamicRecoveryPromptBuilder()
    diagnosis = StructuredDiagnosis(
        tool_name="get_bank_balance_native",
        is_valid=False,
        category=FailureCategory.EXTERNAL_SERVICE_ERROR,
        persistence=PersistenceType.PERMANENT,
        root_cause="Tool 404 Deprecated",
        severity="HIGH",
        recommended_action=RecoveryDirective.REROUTE
    )
    decision = {
        "action": "reroute",
        "suggested_tool": "get_broker_balance_ledger_native",
        "target_path": ["get_broker_balance_ledger_native", "archive_broker_balance_ledger_native", "email_contact_by_name"]
    }
    payload = builder.build_prompt(diagnosis, decision, blacklisted_tools={"get_bank_balance_native"})
    assert "Planned alternative workflow sequence" in payload.prompt_text
    assert "archive_broker_balance_ledger_native" in payload.prompt_text
    print("   [PASS] Full alternative workflow sequence successfully injected into recovery directive.")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING FULL CARE 7-LAYER PIPELINE INTEGRATION TESTS")
    print("==================================================")
    test_layer_4_dag_rerouting()
    test_layer_4_dag_rerouting_toolmaze_dict_format()
    test_layer_5_recovery_prompt_builder()
    test_layer_5_full_workflow_path_injection()
    test_layer_6_loop_detector()
    test_layer_7_selective_verifier()
    test_layer_1_tiered_sov_soft_advisory()
    test_full_care_agent_closed_loop()
    print("==================================================")
    print("ALL 7 LAYERS VERIFIED SUCCESSFULLY (8/8 PASSED)!")
    print("==================================================")



def test_layer_4_rejects_candidates_with_unsatisfied_prerequisites():
    """Do not select a DAG node when its prerequisites have not executed."""
    selector = DAGPathSelector()

    task_json = {
        "task_id": "test_unsatisfied_prerequisites",
        "dag": {
            "nodes": [
                {"tool_name": "publish_booking", "dependencies": ["create_booking"]},
                {"tool_name": "create_booking", "dependencies": ["get_hotel_details"]},
                {"tool_name": "get_hotel_details", "dependencies": ["lookup_hotel"]},
            ]
        },
    }

    candidate = selector.find_reroute(
        failed_tool="failed_tool",
        task_json=task_json,
        blacklisted_tools={"failed_tool"},
        executed_tools=[],
    )

    assert not candidate.is_viable, (
        "Selector should reject rerouting when no candidate has satisfied "
        f"prerequisites, but selected {candidate.selected_tool!r}"
    )


def test_layer_4_strategy_b_rejects_unsatisfied_prerequisites():
    """Strategy B must not select a substitute whose DAG prerequisites are unmet."""
    selector = DAGPathSelector()

    # Configure a known substitute directly, so this test does not depend
    # on the repository's alternatives catalog contents.
    selector._tool_to_alternatives["failed_tool"] = {"publish_booking"}

    task_json = {
        "task_id": "test_strategy_b_unsatisfied_prerequisite",
        "dag": {
            "nodes": [
                {
                    "tool_name": "publish_booking",
                    "dependencies": ["create_booking"],
                },
                {
                    "tool_name": "create_booking",
                    "dependencies": ["get_hotel_details"],
                },
                {
                    "tool_name": "get_hotel_details",
                    "dependencies": ["lookup_hotel"],
                },
            ]
        },
    }

    candidate = selector.find_reroute(
        failed_tool="failed_tool",
        task_json=task_json,
        blacklisted_tools={"failed_tool"},
        executed_tools=[],
    )

    assert not candidate.is_viable, (
        "Strategy B must not select a substitute when its prerequisites "
        f"are unmet; selected {candidate.selected_tool!r}"
    )


def test_layer_4_strategy_a_path_rejects_unsatisfied_prerequisites():
    """Strategy A must not select the next path tool if its DAG prerequisites are unmet."""
    selector = DAGPathSelector()

    task_json = {
        "task_id": "test_strategy_a_path_dependencies",
        "valid_paths": [
            {"path_id": "path_0", "tools": ["failed_tool", "publish_booking"]}
        ],
        "dag": {
            "nodes": [
                {"tool_name": "publish_booking", "dependencies": ["create_booking"]},
                {"tool_name": "create_booking", "dependencies": ["lookup_hotel"]},
            ]
        },
    }

    candidate = selector.find_reroute(
        failed_tool="failed_tool",
        task_json=task_json,
        blacklisted_tools={"failed_tool"},
        executed_tools=[],
    )

    assert not candidate.is_viable, (
        "Strategy A path selection must reject a next tool with unmet prerequisites; "
        f"selected {candidate.selected_tool!r}"
    )


def test_layer_4_strategy_a_explicit_alternative_checks_prerequisites():
    """Strategy A.2 must not bypass DAG prerequisites for explicit alternatives."""
    selector = DAGPathSelector()

    task_json = {
        "task_id": "test_strategy_a_explicit_alternative_dependencies",
        "alternative_tools": ["failed_tool", "publish_booking"],
        "dag": {
            "nodes": [
                {"tool_name": "publish_booking", "dependencies": ["create_booking"]},
                {"tool_name": "create_booking", "dependencies": ["lookup_hotel"]},
            ]
        },
    }

    candidate = selector.find_reroute(
        failed_tool="failed_tool",
        task_json=task_json,
        blacklisted_tools={"failed_tool"},
        executed_tools=[],
    )

    assert not candidate.is_viable, (
        "An explicit alternative with unmet prerequisites must not be selected; "
        f"selected {candidate.selected_tool!r}"
    )


def test_layer_4_rejects_candidate_missing_from_declared_dag():
    """Reject an unlisted substitute when the task explicitly declares a DAG."""
    selector = DAGPathSelector()
    selector._tool_to_alternatives["failed_tool"] = {"unlisted_tool"}

    task_json = {
        "task_id": "test_candidate_missing_from_dag",
        "dag": {
            "nodes": [
                {"tool_name": "lookup_hotel", "dependencies": []},
            ]
        },
    }

    candidate = selector.find_reroute(
        failed_tool="failed_tool",
        task_json=task_json,
        blacklisted_tools={"failed_tool"},
        executed_tools=[],
    )

    assert not candidate.is_viable, (
        "An alternative missing from an explicitly declared DAG "
        "must not be assumed dependency-free."
    )
def test_care_agent_does_not_silently_remap_tool_arguments():
    """A reroute must not reuse arguments when replacement requirements differ."""
    mock_llm = MockBaseAgent()
    agent = CAREAgent(base_agent=mock_llm)

    task_json = {
        "task_id": "reroute_argument_test",
        "task_description": "Retrieve flight information",
        "valid_paths": [
            {"path_id": "original", "tools": ["get_flight_info"]},
            {"path_id": "alternative", "tools": ["get_flight_info_aviationstack"]},
        ],
        "alternative_tools": [
            "get_flight_info",
            "get_flight_info_aviationstack",
        ],
    }

    tool_definitions = [
        {
            "name": "get_flight_info",
            "description": "Original flight lookup",
            "parameters": {
                "type": "object",
                "properties": {"flight_number": {"type": "string"}},
                "required": ["flight_number"],
            },
        },
        {
            "name": "get_flight_info_aviationstack",
            "description": "Alternative flight lookup",
            "parameters": {
                "type": "object",
                "properties": {"flight_iata": {"type": "string"}},
                "required": ["flight_iata"],
            },
        },
    ]

    agent.initialize(
        "Retrieve flight information",
        tool_definitions,
        task_json=task_json,
    )

    # Force the original tool to be blacklisted.
    agent.health_registry.blacklist_tool("get_flight_info")

    mock_llm.action_queue.append(
        AgentAction(
            type="tool_call",
            tool_name="get_flight_info",
            arguments={"flight_number": "AI101"},
        )
    )

    action = agent.step()

    # The replacement requires flight_iata, which cannot safely be inferred
    # from the original schema alone.
    assert not (
        action.tool_name == "get_flight_info_aviationstack"
        and action.arguments == {"flight_number": "AI101"}
    ), "CARE must not silently pass incompatible arguments to a replacement"

def test_reroute_selects_next_tool_on_alternate_path():
    selector = DAGPathSelector()

    task_json = {
        "valid_paths": [
            {"path_id": "A", "tools": ["tool_a", "tool_b", "tool_d"]},
            {"path_id": "B", "tools": ["tool_a", "tool_c", "tool_d"]},
        ]
    }

    candidate = selector.find_reroute(
        failed_tool="tool_b",
        task_json=task_json,
        blacklisted_tools={"tool_b"},
        executed_tools=["tool_a"],
    )

    assert candidate.is_viable
    assert candidate.selected_tool == "tool_c"
    assert candidate.target_path == ["tool_a", "tool_c", "tool_d"]


def test_successful_result_advances_active_path_once():
    mock_agent = MockBaseAgent()
    care = CAREAgent(base_agent=mock_agent, enable_sov=True)

    task = {
        "task_id": "path_progress_test",
        "valid_paths": [
            {"path_id": "A", "tools": ["tool_a", "tool_b"]}
        ],
    }

    care.initialize("Test task", {}, task_json=task)

    assert care.active_path_index == 0
    assert care._expected_tool_for_current_step() == "tool_a"

    mock_agent.action_queue.append(
        AgentAction(
            type="tool_call",
            tool_name="tool_a",
            arguments={}
        )
    )

    action = care.step()
    assert action.tool_name == "tool_a"

    care.receive_tool_result(
        "tool_a",
        {"status": "success", "value": 123}
    )

    assert care.active_path_index == 1
    assert care._expected_tool_for_current_step() == "tool_b"

def test_failed_result_does_not_advance_active_path():
    mock_agent = MockBaseAgent()
    care = CAREAgent(base_agent=mock_agent, enable_sov=True)

    task = {
        "task_id": "failed_progress_test",
        "valid_paths": [
            {"path_id": "A", "tools": ["tool_a", "tool_b"]}
        ],
    }

    care.initialize("Test task", {}, task_json=task)

    care.receive_tool_result(
        "tool_a",
        {"status": "error", "error": "Tool failed"}
    )

    assert care.active_path_index == 0
    assert "tool_a" not in care.completed_tools
    assert care._expected_tool_for_current_step() == "tool_a"


def test_off_path_tool_is_not_returned():
    mock_agent = MockBaseAgent()
    care = CAREAgent(base_agent=mock_agent, enable_sov=False)

    task = {
        "task_id": "off_path_test",
        "valid_paths": [
            {"path_id": "A", "tools": ["tool_a", "tool_b"]}
        ],
    }

    care.initialize("Test task", {}, task_json=task)

    # First proposal is incorrect.
    mock_agent.action_queue.append(
        AgentAction(
            type="tool_call",
            tool_name="tool_c",
            arguments={}
        )
    )

    # Correction proposal is correct.
    mock_agent.action_queue.append(
        AgentAction(
            type="tool_call",
            tool_name="tool_a",
            arguments={}
        )
    )

    action = care.step()

    assert action.type == "tool_call"
    assert action.tool_name == "tool_a"
    assert care.active_path_index == 0

