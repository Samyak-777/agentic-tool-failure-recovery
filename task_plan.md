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

## Phase 3: Remaining Layers Implementation (In Progress)
- [ ] **Layer 4: DAG-Aware Alternative Path Selection** (`ToolMaze/dag_rerouting/`)
  - Build `path_selector.py` to inspect task DAG, alternative tools via `alternatives_loader.py`, and prune blocked paths
- [ ] **Layer 5: Dynamic Recovery Prompts with Evidence** (`ToolMaze/recovery_prompt/`)
  - Build `prompt_builder.py` providing structured failure diagnosis, blacklisted tools, and valid alternatives to agent
- [ ] **Layer 6: Cost-Aware Control & Loop Detection** (`ToolMaze/tool_memory/loop_detector.py`)
  - Implement cycle/ping-pong detection (preventing alternating tool call loops) and enforce budget caps
- [ ] **Layer 7: Selective LLM Verification** (`ToolMaze/selective_verification/`)
  - Lightweight verification module for ambiguous/borderline outputs
- [ ] **Unified CARE Agent** (`ToolMaze/evaluation/agents/care_agent.py`)
  - Implement `CAREAgent` integrating Layers 1–7 into ToolMaze's `BaseAgent` and `ExecutionEngine`

## Phase 4: Verification on Test Cases
- [ ] Unit & integration tests for Layers 4–7 (`ToolMaze/tests/test_full_care_pipeline.py`)
- [ ] Representative end-to-end task tests across C1/C2 (P0, P1, P2, P3, P4)
- [ ] Verify multi-key rotation and rate-limit handling across available Gemini API keys

## Phase 5: Benchmark Evaluation on ToolMaze Dataset
- [ ] Configure `run_eval_care.py` with multi-key pool, batching, and local fallback
- [ ] Run benchmark evaluation across C1–C4 tasks
- [ ] Compare baseline vs CARE architecture (TSR, PRR, RC metrics)
- [ ] Generate comparative analysis and report findings in `progress.md` and `findings.md`
