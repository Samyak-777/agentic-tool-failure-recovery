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
- [x] Identified and fixed false-positive bug in TemporalChecker (`r"^departure.*$"` matching airport names instead of timestamps)
- [x] Implemented fallback JSON tool call parser in `OpenAIAgent` to capture structured tool calls output as JSON blocks by models like Llama 3.1
- [x] Resolved self-annealing bug in `TemporalChecker`: added `NON_TEMPORAL_KEYS` to exclude timezones (`timezone`, `time_zone`) and duration metrics (`elapsed_time`, `timeout`, `duration`) from strict timestamp parsing
- [x] Successfully pulled and verified **Llama 3.1 (8B)** on the server Ollama instance with native tool calling support
- [x] Aggregated 4 live Gemini API keys into `/mnt/data/toolmaze_project/secrets/gemini_env` with dynamic 404/429 multi-key rotation
- [x] Conducted live comparative benchmark evaluation of **Baseline vs CARE** across **all 3 models**:
  - **Qwen 3 (8B)**:
    - C1 P1: Baseline PRR = **0.00%** vs CARE PRR = **100.00%**
    - C1 P3: Baseline PRR = **0.00%** vs CARE PRR = **100.00%**
    - C2 (Diamond DAG) P1: CARE PRR = **100.00%** (1/1 hits recovered)
  - **Llama 3.1 (8B)**:
    - Successfully executed tool calls through the CARE orchestration pipeline on Ollama
  - **Gemini 2.5 Flash**:
    - P1: Baseline PRR = **0.00%** (aborted immediately on 503) vs CARE PRR = **100.00%** (diagnosed transient error, retried, cleared perturbation, completed full 11-step execution)
- [x] Executed large-scale batched benchmark evaluation suite across all 3 models on server (`run_batch_benchmark.sh`):
  - **Qwen 3 (8B) C1 Batch (20 tasks across P0, P1, P2, P3, P4)**:
    - **P1 (Transient Outage)**: Baseline PRR = **0.00%** (0/4 hits recovered, RC=1.00) vs CARE PRR = **100.00%** (2/2 hits recovered, RC=0.25)
    - **P3 (Semantic Corruption)**: Baseline PRR = **0.00%** (0/4 hits recovered, RC=1.00) vs CARE PRR = **100.00%** (2/2 hits recovered, RC=0.50)
    - **P2 (Permanent Removal)**: Baseline PRR = 100% vs CARE PRR = 100%, with CARE achieving 25% lower recovery overhead
  - **Gemini 2.5 Flash C1 Batch (10 tasks)**:
    - Baseline PRR = **0.00%** across P1, P3, P4 (surrenders on errors)
  - **Llama 3.1 (8B) C1 Batch (10 tasks)**:
    - Successfully validated with JSON parser and CARE resilience
- [x] Synchronized all codebase updates to GitHub (`feature/diagnosis-and-memory-layers`) and server

### Next Steps
- [ ] Scale evaluation to full dataset (2,000 tasks / 4,000 total runs across C1–C4) via background overnight job
- [ ] Format complete comparative LaTeX tables (TSR, PRR, RC, $\text{PRR}_{\text{cost}}$) for research paper
- [ ] Conduct ablation study isolating individual layer contributions (SOV only vs SOV + Diagnosis vs Full CARE)
