# SOP: ToolMaze Codebase Architecture

## Overview

ToolMaze is a benchmark framework for evaluating LLM agent fault-tolerance under tool perturbations.
The codebase has three main layers:

---

## 1. Core Runtime (`toolmaze/core/`)

### `context.py` — ExecutionContext
- Maintains execution state: user_input, data store, history
- Records each step: tool name, args, output, status, perturbation flag
- Supports `find_tool_output()` and `find_alternative_output()` for history lookup

### `executor.py` — ToolExecutor
- Loads plugin modules from `tools/plugins/`
- Loads YAML definitions from `tools/definitions/`
- Executes tool calls by dispatching to the correct plugin function

### `types.py` — Data Types
- Tool definitions, parameter schemas, execution results

---

## 2. Evaluation Framework (`evaluation/`)

### `core/sandbox.py` — ExecutionEngine
- **Central orchestrator**: runs agent in controlled perturbation environment
- `InferenceContext`: wraps ExecutionContext to prevent argument leakage
- **Perturbation injection logic**:
  - C1: single perturbation point per task
  - C2/C3: per-path perturbation maps, first-touch activation
  - C4: per-slot first-touch — first tool called in each slot becomes victim
  - P1/P3 (transient): only first call returns corrupted output
  - P2/P4 (persistent): every call returns corrupted output
- Records every round, tool call, perturbation status, and token count

### `core/judge.py` — JudgeEngine
- Uses LLM-as-judge to evaluate task completion
- DAG-based dependency analysis using templates
- Produces pass/fail verdicts with reasoning

### `core/metrics.py` — MetricsCalculator
- **TSR**: `passed_count / total_count` per mode
- **PRR**: `resolved_hits / total_hits` — hit-conditioned recovery rate
  - Hit = first occurrence of perturbed tool in a run
  - Resolved = agent correctly handles: retry (P1/P3), path-switch (P2/P4), abort (C1 permanent)
- **RC**: `1 - C_oracle / max(C_actual, C_oracle)` for hit-and-pass; 1.0 for hit-and-fail; 0.0 for no-hit
  - `C_actual` = tool calls from first perturbation hit to end
  - `C_oracle` = minimum recovery suffix cost from task structure
- **Insights**: Auto-generates natural language findings (trust gap, validation gap, etc.)

### `agents/` — Agent Implementations
- `base_agent.py`: Abstract interface — `initialize()`, `step()`, `receive_tool_result()`, `get_total_tokens()`, `reset()`
- `openai_agent.py`: OpenAI API with native function calling
- `anthropic_agent.py`: Anthropic API with native tool use
- `vllm_agent.py`: **Key for us** — extends OpenAIAgent, uses OpenAI-compatible vLLM endpoint
- `mcp_agent.py`: Prompt-based MCP-style tool calling

### Key Agent Interface:
```python
class BaseAgent(ABC):
    def initialize(task_description, tool_definitions) -> None
    def step(user_message=None) -> AgentAction  # "tool_call" or "final_answer"
    def receive_tool_result(tool_name, result) -> None
    def get_total_tokens() -> int
    def get_token_usage() -> TokenUsage
    def get_conversation_history() -> List[Dict]
    def reset() -> None
```

---

## 3. Tool Corpus (`tools/`)

- 273 tool plugins organized by category
- `definitions/`: YAML specs (Source / Processor / Action types)
- `plugins/`: Executable Python modules
- `loader.py`: Loads tool definitions
- `alternatives_loader.py`: Loads alternative tool mappings for rerouting

---

## How to Add Our Improved Agent

Per `README.md`, to add a new agent:
1. Create `evaluation/agents/care_agent.py` inheriting `BaseAgent`
2. Register in `evaluation/agents/__init__.py`
3. Add branch in `evaluation/scripts/run_eval.py:create_agent()`

Our CARE agent will:
- Wrap the VLLMAgent (composition, not inheritance)
- Intercept `receive_tool_result()` to run SOV checks
- Override `step()` to implement cost-aware recovery routing
- Track additional metrics: recovery_calls, recovery_tokens, strategy_type per step

---

## Key Configuration (`evaluation/configs/eval_config.yaml`)

```yaml
agent:
  type: "vllm"           # We use this for open-source models
  model: "qwen-2.5-7b"   # Model served by vLLM
  base_url: "http://localhost:8000/v1"  # vLLM endpoint
  api_key: "EMPTY"
  temperature: 0.7
  max_tokens: 4096

execution:
  max_rounds: 25          # Max agent steps per task
  timeout_per_round: 1000

evaluation:
  modes: ["P0", "P1", "P2", "P3", "P4"]
  parallel: true
  max_workers: 10
```

---

## Data Flow

```
Task JSON → ExecutionEngine → Agent.initialize(task, tools)
  Loop:
    Agent.step() → AgentAction(tool_call)
    ExecutionEngine: check perturbation → inject/pass → execute tool
    Agent.receive_tool_result(tool_name, result)
    TraceLogger.log(round, tool, args, result, perturbation_status, tokens)
  Until: Agent returns "final_answer" OR max_rounds reached
  
Judge: evaluate(task_json, agent_trace) → pass/fail + reasoning
Metrics: compute TSR, PRR, RC from all task results
```
