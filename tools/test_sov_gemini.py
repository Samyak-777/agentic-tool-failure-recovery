import os
import sys
import json
import time
from pathlib import Path

# Add project roots
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "ToolMaze"))

from ToolMaze.evaluation.agents.openai_agent import OpenAIAgent
from ToolMaze.evaluation.core.sandbox import ExecutionEngine
from ToolMaze.semantic_validation import ValidationConfig

def run_sov_gemini_test(task_file: str, mode_label: str):
    print(f"\n{'='*70}")
    print(f"TESTING SOV LAYER 1 WITH GEMINI API AGENT — [{mode_label}]")
    print(f"Task File: {task_file}")
    print(f"{'='*70}")

    with open(task_file, "r", encoding="utf-8") as f:
        task_json = json.load(f)

    gemini_key = os.environ.get("GEMINI_API_KEY2") or os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY2 or GEMINI_API_KEY must be set!")

    # Initialize OpenAIAgent with Gemini configuration
    agent = OpenAIAgent(
        model="gemini-3.8-flash",
        api_key=gemini_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        temperature=0.0,
        max_tokens=4096
    )

    # Configure Layer 1: SOV
    validation_config = ValidationConfig.from_dict({
        "enabled": True,
        "fail_fast": False,
        "checkers": {
            "schema": {"enabled": True},
            "type": {"enabled": True},
            "required": {"enabled": True},
            "range": {"enabled": True},
            "temporal": {"enabled": True},
            "entity": {"enabled": True},
            "cross_field": {"enabled": True},
            "cross_tool": {"enabled": True},
            "state": {"enabled": True},
            "llm": {"enabled": False}  # deterministic only
        }
    })

    tools_dir = str(project_root / "ToolMaze" / "tools")
    engine = ExecutionEngine(
        task_json=task_json,
        agent=agent,
        tools_dir=tools_dir,
        validation_config=validation_config
    )

    print(f"Task ID: {engine.task_id}")
    print(f"Query: {engine.task_description}")
    print(f"Perturbation Mode: {engine.mode}")
    print(f"SOV Enabled: {engine.semantic_validation_enabled}")

    # Run execution with backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger, token_usage = engine.run(max_rounds=10)
            break
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                print(f"[RETRY {attempt+1}/{max_retries}] Gemini 503 hit, backing off 5s...")
                time.sleep(5)
            else:
                print(f"Execution terminated: {e}")
                raise e

    print("\n--- Execution Steps & SOV Validation Results ---")
    for step in logger.steps:
        print(f"\nStep {step.step_num}:")
        print(f"  Agent Action: {step.agent_action.get('tool_name')} ({step.agent_action.get('arguments')})")
        print(f"  Perturbation Status: {step.perturbation_status}")
        print(f"  Raw Result: {str(step.tool_result)[:120]}...")
        if step.validation_result:
            print(f"  SOV Pipeline Status: {step.validation_result.get('pipeline_status')}")
            violations = step.validation_result.get('violations', [])
            print(f"  SOV Violations Count: {len(violations)}")
            for v in violations:
                print(f"    - [{v.get('checker_name')}] {v.get('message')}")
        else:
            print("  SOV Validation: None")

    print("\n--- Final Summary ---")
    print(f"Total Steps: {len(logger.steps)}")
    print(f"Token Usage: {token_usage}")
    return logger

if __name__ == "__main__":
    c1_dir = project_root / "ToolMaze" / "data" / "perturbed_tasks" / "c1"
    
    # 1. Clean P0 task
    p0_task = next(c1_dir.glob("*_P0.json"))
    # 2. Implicit corrupted P3 task
    p3_task = next(c1_dir.glob("*_P3.json"))
    
    print("Testing clean task P0...")
    run_sov_gemini_test(str(p0_task), "Clean P0 Baseline")
    
    print("\nTesting perturbed task P3 (Implicit Semantic Corruption)...")
    run_sov_gemini_test(str(p3_task), "Corrupted P3 Perturbation")
