# Progress Log — ToolMaze Enhancement Project

## 2026-08-26 | Phase 0: Initialization (Project Pivot)

### Completed
- [x] Project pivoted from C3 (Faithfulness-Audited Reasoning Traces) to ToolMaze Enhancement
- [x] Read and analyzed full ToolMaze paper (arXiv:2606.05806)
- [x] Read and analyzed SWE-Agent paper (arXiv:2405.15793)
- [x] Inspected ToolMaze GitHub repo (github.com/Zhudongsheng75/ToolMaze)
- [x] Identified 7 implicit errors/gaps in the ToolMaze paper
- [x] Defined data schemas (Input/Output/Aggregated) in gemini.md
- [x] Defined metric formulas (TSR, PRR, RC) and improvement targets
- [x] Completed B.L.A.S.T. Discovery Questions (5/5 answered)
- [x] Initialized project memory files (gemini.md, findings.md, progress.md)
- [x] Verified live SSH reachability to server `10.18.1.16` and extracted full hardware specs
- [x] Confirmed GPU: NVIDIA TITAN RTX (24 GB VRAM) + 128 GB System RAM
- [x] Mounted 3.6 TB secondary disk (`/dev/sdb`) to `/mnt/data` with persistent `/etc/fstab` entry
- [x] Created project workspace at `/mnt/data/toolmaze_project/`
- [x] Cloned ToolMaze repository into `/mnt/data/toolmaze_project/ToolMaze`
- [x] Installed Miniconda & Python 3.10 virtual environment (`/mnt/data/toolmaze_project/envs/toolmaze`)
- [x] Installed PyTorch with CUDA 12.1 acceleration, `vllm`, `huggingface_hub`, `openai`, and ToolMaze requirements
- [x] Downloaded official ToolMaze dataset (`c1`–`c4` perturbed tasks + templates) to `/mnt/data/toolmaze_project/ToolMaze/data`:
  - **Perturbed Tasks (2,000 total)**: `c1` (500), `c2` (500), `c3` (500), `c4` (500)
  - **DAG Templates (400 total)**: `c1` (100), `c2` (100), `c3` (100), `c4` (100)
- [x] Verified PyTorch GPU acceleration on NVIDIA TITAN RTX (4096x4096 tensor matmul: SUCCESS)
- [x] Verified ToolMaze tool loader (270 tools indexed across Action, Source, Processor)

### Key Paths on Server (`10.18.1.16`)
- **ToolMaze Codebase**: `/mnt/data/toolmaze_project/ToolMaze`
- **Python 3.10 Env**: `/mnt/data/toolmaze_project/envs/toolmaze`
- **Python Binary**: `/mnt/data/toolmaze_project/envs/toolmaze/bin/python`
- **Pip Binary**: `/mnt/data/toolmaze_project/envs/toolmaze/bin/pip`
- **Benchmark Tasks**: `/mnt/data/toolmaze_project/ToolMaze/data/perturbed_tasks`
- **DAG Templates**: `/mnt/data/toolmaze_project/ToolMaze/data/templates`
- **Model Weights Storage**: `/mnt/data/toolmaze_project/models`

- [x] Tested Layer 1 SOV with live Gemini API agent on server (`tools/test_sov_gemini.py`):
  - Verified real multi-turn function calling with Gemini 3.8 Flash
  - Verified SOV deterministic output interception & violation detection
- [x] Designed and implemented **Layer 2: Structured Failure Diagnosis** (`ToolMaze/diagnosis/`):
  - `taxonomy.py`: Hierarchical failure categories, persistence types (`TRANSIENT` vs `PERMANENT`), and `StructuredDiagnosis` model
  - `engine.py`: StructuredDiagnosisEngine classifying failure category and root cause
- [x] Designed and implemented **Layer 3: Failure-State Tracking, Tool Memory & Recovery Controller** (`ToolMaze/tool_memory/`):
  - `registry.py`: `ToolHealthRegistry` (`HEALTHY`, `DEGRADED`, `BLACKLISTED`)
  - `memory.py`: `ToolMemory` (cached outputs and tried argument signatures)
  - `budget.py`: `BudgetTracker` (enforces max call and recovery allowances)
  - `recovery_controller.py`: `RecoveryController` mapping diagnoses to concrete action pathways (`CONTINUE`, `RETRY`, `VERIFY`, `REROUTE`, `ABORT`)
- [x] Created and verified end-to-end integration test suite (`tools/test_all_three_layers.py` and `ToolMaze/tests/test_layers_2_and_3.py`):
  - Clean execution -> CONTINUE (PASSED)
  - Transient anomaly -> RETRY (PASSED)
  - Persistent anomaly -> BLACKLIST & REROUTE (PASSED)
  - Budget cap -> ABORT (PASSED)
- [x] Pushed all code to GitHub branch `feature/diagnosis-and-memory-layers` and deployed to server (`10.18.1.16`)

- [x] Designed and implemented **Layer 4: DAG-Aware Alternative Path Selection** (`ToolMaze/dag_rerouting/`):
  - `path_selector.py`: Topological DAG traversal, pre-computed solution path filtering, and dependency satisfaction checks
- [x] Designed and implemented **Layer 5: Dynamic Recovery Prompts with Evidence** (`ToolMaze/recovery_prompt/`):
  - `prompt_builder.py`: Synthesizes evidence-rich diagnostic payloads replacing generic error strings
- [x] Designed and implemented **Layer 6: Cost-Aware Control & Loop Detection** (`ToolMaze/tool_memory/loop_detector.py`):
  - `loop_detector.py`: Detects immediate repetition, ping-pong oscillation ($A \to B \to A \to B$), and multi-step cycles
- [x] Designed and implemented **Layer 7: Selective LLM Verification** (`ToolMaze/selective_verification/`):
  - `verifier.py`: Invoked exclusively on ambiguous / borderline semantic outputs to preserve token budget
- [x] Designed and implemented **CAREAgent** (`ToolMaze/evaluation/agents/care_agent.py`):
  - Integrates all 7 layers of resilience into ToolMaze's `BaseAgent` and `ExecutionEngine`
- [x] Implemented and verified comprehensive 7-layer test suite (`ToolMaze/tests/test_full_care_pipeline.py`):
  - 5/5 test cases passed on both local environment and server
- [x] Implemented multi-key rotating evaluation runner (`ToolMaze/evaluation/scripts/run_eval_care.py`):
  - Thread-safe key pool with exponential backoff on 429
  - Verified live task execution on server with full trace logging and metrics calculation
- [x] Synchronized all codebase changes with GitHub branch `feature/diagnosis-and-memory-layers` and deployed to server

### Next Steps
- [ ] Run benchmark evaluation across full task sets (C1, C2, C3, C4) comparing CARE vs Baseline
- [ ] Confirm location/keys for the 6-7 Gemini API keys env file to maximize parallel evaluation throughput
- [ ] Collate TSR, PRR, and RC comparative metrics for paper draft
