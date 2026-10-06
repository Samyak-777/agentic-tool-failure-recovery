"""
Comprehensive End-to-End Integration Test for Layers 1, 2, and 3:
- Layer 1: Deterministic Semantic Output Validation (SOV)
- Layer 2: Structured Failure Diagnosis
- Layer 3: Failure-State Tracking, Tool Memory & Recovery Controller
"""

import sys
from pathlib import Path

# Add project roots
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "ToolMaze"))

from semantic_validation import SemanticValidationPipeline, ValidationConfig
from tools.loader import ToolLoader
from diagnosis import StructuredDiagnosisEngine, RecoveryDirective
from tool_memory import (
    ToolHealthRegistry,
    ToolMemory,
    BudgetTracker,
    BudgetConfig,
    RecoveryController
)

def run_integrated_pipeline_test():
    print("=" * 80)
    print("TESTING 3-LAYER SYSTEMS-LEVEL ORCHESTRATION PIPELINE")
    print("=" * 80)

    # 1. Initialize ToolLoader & Layer 1 SOV Pipeline
    tools_dir = project_root / "ToolMaze" / "tools"
    tool_loader = ToolLoader(str(tools_dir / "definitions"))
    
    val_config = ValidationConfig.from_dict({
        "enabled": True,
        "fail_fast": False,
        "checkers": {
            "schema": {"enabled": True},
            "type": {"enabled": True},
            "required": {"enabled": True},
            "range": {"enabled": True},
            "temporal": {"enabled": True},
            "cross_field": {"enabled": True},
        }
    })
    sov_pipeline = SemanticValidationPipeline(val_config, tool_loader)

    # 2. Initialize Layer 2 Diagnosis Engine
    diagnosis_engine = StructuredDiagnosisEngine(max_transient_retries=1)

    # 3. Initialize Layer 3 Components
    health_registry = ToolHealthRegistry(failure_threshold_to_blacklist=2)
    tool_memory = ToolMemory()
    budget_tracker = BudgetTracker(BudgetConfig(
        max_total_tool_calls=10,
        max_recovery_attempts=3,
        max_retries_per_tool=1
    ))
    
    # Tool alternatives mapping for stock retrieval
    alt_map = {
        "get_stock_yahoo_finance": ["get_stock_alpha_vantage", "get_stock_finnhub"]
    }
    controller = RecoveryController(
        health_registry=health_registry,
        memory=tool_memory,
        budget_tracker=budget_tracker,
        alternative_tools_map=alt_map
    )

    sov_pipeline.create_execution_state("exec_demo_1", "task_c1_stock")
    tool_name = "get_stock_yahoo_finance"
    args = {"symbol": "AAPL"}

    # =========================================================================
    # SCENARIO A: Clean Tool Execution (Branch 1 -> CONTINUE)
    # =========================================================================
    print("\n--- SCENARIO A: Clean Tool Execution ---")
    clean_output = {"price_usd": 182.50, "currency": "USD"}
    
    val_res = sov_pipeline.validate(
        tool_name=tool_name,
        arguments=args,
        result=clean_output,
        execution_id="exec_demo_1",
        task_id="task_c1_stock",
        step=1
    )
    print(f"[Layer 1 SOV] Status: {val_res.pipeline_status.value}")
    
    diagnosis = diagnosis_engine.diagnose(
        tool_name=tool_name,
        arguments=args,
        raw_result=clean_output,
        validation_result=val_res.to_dict(),
        step_num=1
    )
    print(f"[Layer 2 Diagnosis] Valid: {diagnosis.is_valid} | Root Cause: {diagnosis.root_cause}")
    
    decision = controller.decide_recovery(diagnosis, args, step_num=1)
    print(f"[Layer 3 Controller] Directive: {decision['action'].upper()} | Rationale: {decision['rationale']}")
    assert decision["action"] == "continue", f"Scenario A failed: got {decision['action']}"
    print("[PASS] Scenario A: Clean output verified and passed.")

    # =========================================================================
    # SCENARIO B: First-Touch Semantic Anomaly (P3 Transient -> RETRY)
    # =========================================================================
    print("\n--- SCENARIO B: Transient Semantic Anomaly (P3 Negative Price) ---")
    corrupt_output = {"price_usd": -99.99, "currency": "USD"}
    
    val_res = sov_pipeline.validate(
        tool_name=tool_name,
        arguments=args,
        result=corrupt_output,
        execution_id="exec_demo_1",
        task_id="task_c1_stock",
        step=2
    )
    print(f"[Layer 1 SOV] Status: {val_res.pipeline_status.value}")
    print(f"             Failed Checks: {val_res.failed_checks}")
    print(f"             Reason: {val_res.reason}")
    assert val_res.pipeline_status.value == "INVALID", "SOV should catch negative price!"
    
    diagnosis = diagnosis_engine.diagnose(
        tool_name=tool_name,
        arguments=args,
        raw_result=corrupt_output,
        validation_result=val_res.to_dict(),
        step_num=2
    )
    print(f"[Layer 2 Diagnosis] Category: {diagnosis.category.value} | Persistence: {diagnosis.persistence.value.upper()}")
    print(f"                    Root Cause: {diagnosis.root_cause}")
    assert diagnosis.category.value == "semantic_range_error"
    assert diagnosis.persistence.value == "transient"
    
    decision = controller.decide_recovery(diagnosis, args, step_num=2)
    print(f"[Layer 3 Controller] Directive: {decision['action'].upper()} | Target: {decision['suggested_tool']}")
    print(f"                     Guidance: {decision['agent_prompt_guidance']}")
    assert decision["action"] == "retry", f"Scenario B failed: got {decision['action']}"
    print("[PASS] Scenario B: Transient range anomaly caught -> 1 retry directive issued.")

    # =========================================================================
    # SCENARIO C: Second Consecutive Anomaly (P4 Permanent -> BLACKLIST & REROUTE)
    # =========================================================================
    print("\n--- SCENARIO C: Persistent Anomaly (P4 Corruption -> REROUTE) ---")
    val_res = sov_pipeline.validate(
        tool_name=tool_name,
        arguments=args,
        result=corrupt_output,
        execution_id="exec_demo_1",
        task_id="task_c1_stock",
        step=3
    )
    diagnosis = diagnosis_engine.diagnose(
        tool_name=tool_name,
        arguments=args,
        raw_result=corrupt_output,
        validation_result=val_res.to_dict(),
        tool_call_history=[{"tool_name": tool_name, "is_valid": False}],
        step_num=3
    )
    print(f"[Layer 2 Diagnosis] Category: {diagnosis.category.value} | Persistence: {diagnosis.persistence.value.upper()}")
    print(f"                    Root Cause: {diagnosis.root_cause}")
    assert diagnosis.persistence.value == "permanent"
    
    decision = controller.decide_recovery(diagnosis, args, step_num=3)
    print(f"[Layer 3 Controller] Tool Health: {health_registry.get_record(tool_name).status.value.upper()}")
    print(f"                     Directive: {decision['action'].upper()} -> Substitute: {decision['suggested_tool']}")
    print(f"                     Guidance: {decision['agent_prompt_guidance']}")
    assert decision["action"] == "reroute", f"Scenario C failed: got {decision['action']}"
    assert decision["suggested_tool"] == "get_stock_alpha_vantage", f"Should reroute to alpha_vantage, got {decision['suggested_tool']}"
    print("[PASS] Scenario C: Recurring anomaly classified permanent -> tool blacklisted & rerouted to alternative.")

    # =========================================================================
    # SCENARIO D: Exhaustion of Recovery Budget (-> ABORT)
    # =========================================================================
    print("\n--- SCENARIO D: Recovery Budget Exhaustion ---")
    budget_tracker.recovery_attempts = 3  # Hit max recovery limit
    decision = controller.decide_recovery(diagnosis, args, step_num=4)
    print(f"[Layer 3 Controller] Directive: {decision['action'].upper()}")
    print(f"                     Guidance: {decision['agent_prompt_guidance']}")
    assert decision["action"] == "abort", f"Scenario D failed: got {decision['action']}"
    print("[PASS] Scenario D: Budget cap triggered -> infinite loops prevented.")

    print("\n" + "=" * 80)
    print("🏆 ALL 3 LAYERS VERIFIED & ORCHESTRATING PERFECTLY TOGETHER!")
    print("=" * 80)

if __name__ == "__main__":
    run_integrated_pipeline_test()
