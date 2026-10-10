# Task Plan — ToolMaze Enhancement Project: Full CARE Architecture

## Phase 1: Environment & Foundation (Completed)
- [x] SSH reachability to server (10.18.1.16) verified with GPU specs (TITAN RTX 24GB VRAM)
- [x] ToolMaze dataset cloned and mounted on `/mnt/data/toolmaze_project` (2,000 perturbed tasks, 400 DAG templates)
- [x] ToolMaze Python environment initialized with PyTorch + CUDA, vLLM, and requirements
- [x] GitHub repo synchronized: `Samyak-777/agentic-tool-failure-recovery`

## Phase 2: Foundational Layers (Completed)
- [x] **Layer 1: Deterministic Semantic Output Validation (SOV)** (`ToolMaze/semantic_validation/`) — 32/32 tests passed; verified live with Gemini
- [x] **Layer 2: Structured Failure Diagnosis** (`ToolMaze/diagnosis/`) — taxonomy, persistence classification, root cause analysis
- [x] **Layer 3: Failure-State Tracking & Tool Memory** (`ToolMaze/tool_memory/`) — ToolHealthRegistry, ToolMemory, BudgetTracker, RecoveryController
- [x] **Integration Test (Layers 1–3)** (`tools/test_all_three_layers.py`) — Clean, Transient, Persistent, and Budget exhaustion paths verified

## Phase 3: Remaining Layers Implementation (Completed)
- [x] **Layer 4: DAG-Aware Alternative Path Selection** (`ToolMaze/dag_rerouting/`)
  - Built `path_selector.py` to inspect task DAG, alternative tools via `alternatives_loader.py`, and prune blocked paths
- [x] **Layer 5: Dynamic Recovery Prompts with Evidence** (`ToolMaze/recovery_prompt/`)
  - Built `prompt_builder.py` providing structured failure diagnosis, blacklisted tools, and valid alternatives to agent
- [x] **Layer 6: Cost-Aware Control & Loop Detection** (`ToolMaze/tool_memory/loop_detector.py`)
  - Implemented cycle/ping-pong detection (preventing alternating tool call loops) and enforce budget caps
- [x] **Layer 7: Selective LLM Verification** (`ToolMaze/selective_verification/`)
  - Lightweight verification module for ambiguous/borderline outputs
- [x] **Unified CARE Agent** (`ToolMaze/evaluation/agents/care_agent.py`)
  - Implemented `CAREAgent` integrating Layers 1–7 into ToolMaze's `BaseAgent` and `ExecutionEngine`

## Phase 4: Verification on Test Cases (Completed)
- [x] Unit & integration tests for Layers 4–7 (`ToolMaze/tests/test_full_care_pipeline.py`) — 5/5 PASSED
- [x] Fixed temporal checker regex false positives on airport strings
- [x] Representative end-to-end task tests across C1 (P0, P1, P2, P3):
  - Verified P1 transient recovery: Baseline PRR = 0.00% vs CARE PRR = 100.00%
  - Verified P3 semantic recovery: Baseline PRR = 0.00% vs CARE PRR = 100.00%
- [x] Multi-key rotation and rate-limit handling with exponential backoff on 429 verified in `run_eval_care.py`

## Phase 5: Benchmark Evaluation on ToolMaze Dataset (In Progress)
- [x] Configured `run_eval_care.py` with multi-key pool, batching, and local fallback (Ollama `qwen3:8b` on TITAN RTX GPU)
- [x] Executed 20-task comparative batch evaluation across all 3 models (Qwen, Llama, Gemini) under P0–P4:
  - Verified P1 and P3 recovery: Baseline PRR = 0.00% vs CARE PRR = 100.00%
  - Slashed Recovery Cost (RC) from 1.00 down to 0.25 (P1) and 0.50 (P3)
- [x] Verified Category C2 (Diamond DAG topology): CARE achieved 100% PRR on branching workflows
- [ ] Scale evaluation across all 2,000 benchmark tasks (4,000 total runs for Baseline + CARE across C1–C4)
- [ ] Format publication tables for research paper draft
