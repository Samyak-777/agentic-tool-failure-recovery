# Findings — ToolMaze Enhancement Project

## Date: 2026-08-26

---

## Research Discoveries

### Core Paper: ToolMaze (arXiv:2606.05806, Jun 2026)

**Authors**: Dongsheng Zhu, Xuchen Ma, Yucheng Shen, Xiang Li, Yukun Zhao, Shuaiqiang Wang, Lingyong Yan, Dawei Yin
**Affiliations**: Shanghai AI Laboratory, Baidu Inc., East China Normal University, Soochow University, Shandong University

**Key Framework Design**:
- Two-dimensional evaluation: Topological Complexity (𝒞1–𝒞4) × Perturbation Mode (𝒫1–𝒫4)
- DAG-based task generation pipeline: Assembly → Solution-Space Enumeration → Task Naturalisation
- Runtime Perturbation Engine with deterministic injection at pre-specified nodes
- Three metrics: TSR, PRR, RC

**Critical Findings from Paper**:
1. PRR drops ~37% under implicit semantic failures (P3/P4) — agents over-trust corrupted outputs
2. Fault-tolerance scales 3.66× slower than basic task execution with model size
3. Complex topologies (C3/C4) trap agents in futile trial-and-error loops
4. Failure-aware prompting helps but does not close the gap
5. Agentic fault-tolerance is a DISTINCT bottleneck — not solved by scaling or prompting alone

### Reference Paper: SWE-Agent (arXiv:2405.15793, May 2024)

**Authors**: John Yang, Carlos E. Jimenez, Alexander Wettig, Kilian Lieret, Shunyu Yao, Karthik Narasimhan, Ofir Press
**Key Contribution**: Agent-Computer Interface (ACI) design significantly impacts agent performance
**Relevance**: ACI patterns can be adapted for ToolMaze to give agents better error visibility

---

## Identified Implicit Errors / Gaps in ToolMaze Paper

### Gap 1: No Cost-Aware Recovery Optimization
- **Issue**: Paper defines RC but treats it as a passive measurement metric, not an optimization target
- **Impact**: Agents that retry 20× vs 3× and both succeed get same PRR score = 1.0
- **Our Fix**: Introduce cost-weighted PRR: PRR_cost = PRR × (1 / log(1 + RC))

### Gap 2: Over-Trust Detection Is Left to the Agent's Native Reasoning
- **Issue**: Paper identifies the over-trust problem (PRR drops 37% under implicit failures) but provides no detection mechanism
- **Impact**: Agents blindly propagate semantically corrupted values
- **Our Fix**: Implement output validation layer with semantic consistency checks (value range, cross-reference, temporal coherence)

### Gap 3: Static Perturbation Profiles
- **Issue**: Perturbations are injected at fixed pre-specified nodes — real-world failures are more dynamic
- **Impact**: Agent may learn to "memorize" which tools fail rather than developing true resilience
- **Our Fix**: Add a P5 "dynamic/cascading" perturbation mode where failure at node X triggers partial corruption at downstream nodes

### Gap 4: No Recovery Strategy Classification
- **Issue**: Paper doesn't differentiate between recovery strategies (retry, reroute, backtrack, give-up)
- **Impact**: Can't tell if the agent is doing intelligent replanning vs. random walk
- **Our Fix**: Tag each recovery action and compute strategy distribution per model/perturbation type

### Gap 5: Single-Turn Tool Calls Only
- **Issue**: ToolMaze simulates tools as synchronous single-turn function calls
- **Impact**: Misses real-world scenarios where tools have latency, rate limits, partial responses
- **Our Fix for Cloud Phase**: Wrap ToolMaze tools in real HTTP endpoints with realistic failure modes

### Gap 6: No Comparison with Agentic Frameworks
- **Issue**: Paper evaluates raw LLMs (GPT-4o, Claude-3.5, Qwen, etc.) directly, not agent frameworks like SWE-Agent, ReAct, Reflexion
- **Impact**: Unclear how agent scaffolding affects recovery behavior
- **Our Fix**: Benchmark at least 2 agent frameworks (SWE-Agent-style ACI + ReAct baseline)

### Gap 7: Reproducibility Concerns with LLM-Generated Tasks
- **Issue**: Task naturalization uses LLM (Step 3 in pipeline) — different LLM versions may produce different tasks
- **Impact**: Benchmark may not be fully reproducible across time
- **Our Fix**: Pin and document exact LLM version, temperature, and seed for task generation; provide pre-generated task cache

---

## Related Work (2026 Landscape)

| Work | Relevance | Gap Filled |
|---|---|---|
| AgentDebug (OpenReview 2026) | Targeted feedback for specific failure modes | Complements our recovery strategy classification |
| Echo-state-network failure detection (arXiv 2026) | Real-time agent failure detection via telemetry | Low-cost alternative to LLM-as-judge for detecting loops |
| Terminal-Bench | Shell environment robustness benchmark | Validates tool-use resilience in real environments |
| LangGraph / CrewAI circuit breakers | Stateful recovery with retry/timeout policies | Industry-standard patterns we can adopt |
| SWE-bench Pro | Harder, professional repository evaluation | Different domain but similar evaluation philosophy |

---

## Server Specifications (Verified Live via SSH on 2026-08-26)

| Field | Verified Specification |
|---|---|
| **IP Address** | `10.18.1.16` (Reachable from local subnet `172.25.100.59`) |
| **User** | `mrunmayee` (SSH password authenticated) |
| **OS** | Ubuntu 24.04.3 LTS (Noble Numbat), Kernel Linux x86_64 |
| **CPU** | Intel(R) Core(TM) i9-9900K @ 3.60GHz (8 cores / 16 threads, up to 5.0 GHz) |
| **RAM** | **128 GB** (125 GiB total, 121 GiB available) |
| **GPU** | **NVIDIA TITAN RTX (24 GB VRAM / 24,576 MiB)** (Driver 595.84, CUDA 13.2 compatible) |
| **Primary Disk (`/dev/sda2`)** | 930.5 GB ext4 (OS / system partition) |
| **Secondary Disk (`/dev/sdb`)** | **3.6 TB ext4 (Mounted at `/mnt/data`)** — **3.4 TB free and write-verified** |
| **Python** | Python 3.12.3 installed |
| **Docker** | Docker version 29.1.3 installed |

> ✅ **GPU Verdict**: The **24 GB NVIDIA TITAN RTX** with **128 GB RAM** is **ideal** for serving **Qwen-2.5-7B-Instruct** or **Llama-3.1-8B-Instruct** with vLLM under FP16/BF16 precision without quantization loss.
> ✅ **Storage Status**: `/dev/sdb` has been successfully mounted to `/mnt/data` with persistent `/etc/fstab` configuration, providing **3.4 TB free storage** with full user write permissions for models, conda environments, and datasets.
