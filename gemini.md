# gemini.md — Project Constitution: ToolMaze Enhancement

> **This file is LAW.** All code, experiments, and decisions must conform to this document.
> Last Updated: 2026-08-26

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Title** | Enhanced ToolMaze: Improving Dynamic Replanning and Anomaly Recovery in LLM Agents with Cost-Aware Recovery |
| **Base Paper** | "When Tools Fail: Benchmarking Dynamic Replanning and Anomaly Recovery in LLM Agents" (arXiv:2606.05806, Jun 2026) |
| **Reference Paper** | "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering" (arXiv:2405.15793, May 2024) |
| **North Star** | A publishable paper with improved ToolMaze metrics (TSR, PRR, RC) validated on college server + cloud |
| **Timeline** | 3–4 months (Sept 2026 → Dec 2026 / Jan 2027) |
| **Infrastructure** | College Server @ 10.18.1.16 (primary) → Cloud deployment for real-world RCA (secondary) |
| **LLM Backend** | Open-source models only (Llama-3.1, Qwen-2.5, etc.) — self-hosted on college server |

---

## 2. Data Schemas

### 2.1 ToolMaze Task Instance (Input)

```json
{
  "task_id": "string",
  "task_description": "string (natural language query)",
  "dag": {
    "nodes": [
      {
        "tool_id": "string",
        "tool_name": "string",
        "tool_description": "string",
        "parameters": { "param_name": "type" },
        "dependencies": ["tool_id_1", "tool_id_2"]
      }
    ],
    "edges": [["source_tool_id", "target_tool_id"]],
    "perturbation_nodes": ["tool_id_X"]
  },
  "complexity_level": "C1 | C2 | C3 | C4",
  "perturbation_mode": "P0_none | P1_explicit_transient | P2_explicit_permanent | P3_implicit_transient | P4_implicit_permanent",
  "valid_solution_paths": [
    ["tool_sequence_path_1"],
    ["tool_sequence_path_2"]
  ],
  "ground_truth_answer": "string"
}
```

### 2.2 Agent Execution Trace (Output)

```json
{
  "task_id": "string",
  "model_id": "string",
  "agent_variant": "baseline | improved",
  "trace": [
    {
      "step": 1,
      "action": "tool_call | replan | backtrack | give_up",
      "tool_id": "string | null",
      "tool_input": {},
      "tool_output": {},
      "perturbation_encountered": true,
      "perturbation_type": "explicit | implicit | none",
      "tokens_consumed": 1234,
      "latency_ms": 456,
      "timestamp": "ISO8601"
    }
  ],
  "final_answer": "string",
  "metrics": {
    "tsr": 0.0,
    "prr": 0.0,
    "rc_agent_calls": 0,
    "rc_tokens": 0,
    "rc_time_ms": 0,
    "rc_normalized": 0.0
  }
}
```

### 2.3 Experiment Result (Aggregated)

```json
{
  "experiment_id": "string",
  "model_id": "string",
  "agent_variant": "baseline | improved",
  "complexity_level": "C1 | C2 | C3 | C4",
  "perturbation_mode": "P0 | P1 | P2 | P3 | P4",
  "n_tasks": 100,
  "tsr_mean": 0.0,
  "tsr_std": 0.0,
  "prr_mean": 0.0,
  "prr_std": 0.0,
  "rc_mean": 0.0,
  "rc_std": 0.0,
  "rc_agent_calls_mean": 0.0,
  "rc_tokens_mean": 0.0,
  "rc_time_mean_ms": 0.0,
  "total_api_cost_usd": 0.0
}
```

---

## 3. Metric Definitions (from ToolMaze Paper, Section 3.5)

### 3.1 Task Success Rate (TSR)
- **Definition**: Binary — 1 if the agent's final answer matches the ground truth, 0 otherwise.
- **Constraint**: TSR must NOT decrease from baseline in our improved system.

### 3.2 Perturbation Recovery Rate (PRR)
- **Definition**: PRR = (# tasks where agent successfully recovers from perturbation and reaches correct answer) / (# tasks where perturbation was injected)
- **Key Insight from Paper**: PRR plummets ~37% under implicit semantic failures (P3, P4).
- **Our Target**: Statistically significant improvement in PRR across ALL perturbation modes, especially P3/P4.

### 3.3 Recovery Cost (RC)
- **Definition**: Measures the overhead incurred by an agent during recovery from perturbations.
- **Decomposed into**:
  1. **RC_calls**: Number of additional agent tool calls invoked during recovery (beyond the optimal path length)
  2. **RC_tokens**: Total token consumption during replanning and recovery phases
  3. **RC_time**: Wall-clock time for recovery
- **Our Target**: Minimize RC while improving or maintaining PRR.

---

## 4. Perturbation Taxonomy (2×2 Matrix)

| | **Transient** (clears after retry) | **Permanent** (persists; must reroute) |
|---|---|---|
| **Explicit** (error codes, exceptions) | P1: HTTP 429/timeout → retry works | P2: Tool permanently removed → must find alternative |
| **Implicit** (structurally valid, semantically wrong) | P3: Stale data, negative stock counts → retry with validation | P4: Consistently corrupted output → must detect + reroute |

---

## 5. Topological Complexity Levels

| Level | DAG Structure | Recovery Paths |
|---|---|---|
| C1 | Linear chain (4 nodes) | 1 alternative path |
| C2 | Diamond / parallel branches | 2–3 alternative paths |
| C3 | Multi-layered DAG | 3–5 alternative paths |
| C4 | Complex mesh with cycles removed | 5+ alternative paths |

---

## 6. Architectural Invariants

1. **Deterministic Perturbation Injection**: Perturbations are injected at pre-specified nodes, NOT randomly.
2. **Exhaustive Solution Enumeration**: Every task instance must have a pre-computed set of ALL valid solution paths.
3. **Separation of Concerns**: Benchmark harness ≠ Agent logic ≠ Recovery mechanism.
4. **Open-Source Only**: No proprietary API calls for the agent backbone.
5. **Reproducibility**: Every experiment must produce identical results given the same seed.
6. **Cost Accounting**: Every LLM call must be instrumented for token count and latency.

---

## 7. Behavioral Rules

- **DO NOT** submit any result without comparing against the baseline on the SAME task set.
- **DO NOT** modify the ToolMaze benchmark tasks; only modify the agent behavior.
- **DO NOT** use mock/simulated tool outputs for final evaluation — must use real tool execution.
- **DO** log every agent step with full token counts and latency.
- **DO** run each experiment 3× with different seeds and report mean ± std.
- **DO** version control every experiment config in git.
