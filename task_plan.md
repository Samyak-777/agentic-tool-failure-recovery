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
- [x] Implemented evaluation caching/resumption logic in `run_eval_care.py` to prevent duplicate computations across runs
- [x] Launched full-scale benchmark execution suite (`run_full_benchmark_suite.sh`) in background on server:
  - [x] **Phase 1: Qwen 3 (8B) Full Benchmark (C1–C4, 4,000 Tasks)**: Completed 100%. Demonstrates 10.3×–17.4× gain in P1 transient resilience and 3.5×–18.4× gain in P3 semantic corruption defense.
  - [x] **Phase 3: Gemma 4 (31B-IT) Frontier API Benchmark**: Completed 100% across all C1–C4 topologies. CARE achieves 100.0% P1 recovery on C3/C4 (vs 0% baseline) and halves recovery costs.
  - [x] **Comprehensive FYP Professor Report Generated (`CARE_Final_Year_Project_Report.docx`)**: ~3,000 words, 9 tables, professional styling, covering from first principles through benchmark results, failure analysis, and fixes.
- [ ] Push full results, metrics reports, and documentation updates to GitHub
- [ ] Collate complete comparative LaTeX publication tables across all model families and topologies

## Phase 6: Reeti Branch Improvements Evaluation (Active)
- [x] Investigate Reeti's branch `experiment/recovery-tsr-improvements-reeti` on remote server (`10.18.1.16`)
- [x] Analyze 4 targeted failure modes: incomplete workflow execution, P3 corrupted outputs passing schema validation, recovery decisions not leading to alternative paths, premature aborts
- [x] Fix missing method `blacklist_tool` in `ToolMaze/tool_memory/registry.py` on server
- [x] Fix argument compatibility checking in `ToolMaze/evaluation/agents/care_agent.py` to prevent silent incompatible argument reuse
- [x] Verify all 22 regression and integration tests pass (14/14 in `test_full_care_pipeline.py`, 8/8 in `test_layers_2_and_3.py`)
- [x] Restore NVIDIA TITAN RTX driver module for kernel 7.0.0-38 and free 90GB root disk space
- [x] Add `--output-dir` CLI parameter to `run_eval_care.py` to isolate results in `evaluation/results_reeti`
- [x] Verify single-task baseline and CARE execution end-to-end
- [x] Launch 250 Baseline tasks on Category C2 (`run_reeti_eval_250.sh`)
- [x] Launch 250 CARE tasks on Category C2
- [x] Extract and present comparative TSR, PRR, RC metrics table (Original Qwen 3 (8B) vs Reeti's Improved CARE)




