# ToolMaze

This project is from the paper "[When Tools Fail: Benchmarking Dynamic Replanning and Anomaly Recovery in LLM Agents
](https://arxiv.org/abs/2606.05806)". 
Evaluation framework for testing LLM agents on C1/C2/C3/C4 tool-use tasks
under P0–P4 perturbation modes. The framework runs an agent inside a
sandboxed tool runtime, intercepts tool calls to inject perturbations, and
scores the result with a complexity-aware judge.

## Project Layout

```
ToolMaze/
├── toolmaze/              # Core runtime (ExecutionContext, ToolExecutor, ...)
├── tools/                 # Tool plugins (273 plugins) and YAML definitions
│   ├── definitions/       # Tool spec YAMLs (Source / Processor / Action)
│   └── plugins/           # Executable plugin modules
├── data/
│   ├── perturbed_tasks/   # Task JSONs grouped by complexity (c1..c4)
|   ├── tasks/             # Task JSONs generated from templates
│   └── templates/         # DAG templates used by the judge
├── evaluation/
│   ├── core/              # sandbox.py, judge.py, metrics.py
│   ├── agents/            # OpenAI / Anthropic / VLLM / MCP agents
│   ├── utils/             # trace_logger, result_saver
│   ├── configs/           # YAML configs
│   ├── scripts/           # run_eval.py, find_failed_inferences.py
│   └── results/           # Output directory (auto-populated)
├── run_api_eval.py        # Single-model API-based runner
├── run_batch_api_eval.py  # Multi-model concurrent runner with retry loop
└── requirements.txt
```

## Quick Start

### 1. Install dependencies

```bash
conda create -n toolmaze python=3.10 -y
conda activate toolmaze
pip install -r requirements.txt
```

### 2. Configure API credentials

Edit `evaluation/configs/openai_eval_config_c1.yaml`:

```yaml
agent:
  type: "openai"          # or "anthropic", "vllm", "mcp"
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  base_url: "https://api.openai.com/v1"

judge:
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  base_url: "https://api.openai.com/v1"
```

```bash
export OPENAI_API_KEY="your-key"
```

### 3. Download dataset

You can download the dataset from [this link](https://huggingface.co/datasets/dongsheng/ToolMaze) and unzip it into `data`.

### 4. Run evaluation

**Single task / category:**

```bash
# Single task (category auto-inferred from task ID)
python evaluation/scripts/run_eval.py --task-id C1_task_001_P0

# All P0 tasks in c1
python evaluation/scripts/run_eval.py --modes P0

# Full c3 sweep
python evaluation/scripts/run_eval.py --task-category c3 --modes P0 P1 P2 P3 P4

# Override agent + model from CLI
python evaluation/scripts/run_eval.py --agent-type openai --model gpt-4o --modes P0 P1
```

**Single model, all categories (uses `evaluation/configs/openai_eval_config_c1.yaml`
as the base config and overrides agent fields):**

```bash
python run_api_eval.py --models gpt-4o
python run_api_eval.py --models gpt-4o --categories c3 c4
python run_api_eval.py --models gpt-4o --modes P2 P4
```

**Concurrent batch over multiple models (with delete-and-retry):**

Edit the `MODELS` dict at the top of
`run_batch_api_eval.py`, then:

```bash
python run_batch_api_eval.py
python run_batch_api_eval.py --categories c3 c4
python run_batch_api_eval.py --modes P2 P4
```

## Output Files

Results are saved under `evaluation/results/{model}/{fc|mcp}/{c1|c2|c3|c4}/`:

```
inferences/{task_id}_{mode}_inference.json   # Full message trace + token usage
evaluations/{task_id}_{mode}_eval.json       # Judge verdict + reasoning
metrics/metrics_report_{timestamp}.json      # Aggregated TSR / PRR / RC
reports/                                     # Optional text reports
```

`fc` = native function calling agents (openai / anthropic / vllm).
`mcp` = prompt-based MCP-style tool calling.

## Metrics

**TSR (Task Success Rate)**

```
TSR_mode = Count(Pass runs in mode) / Total runs in mode
```

**PRR (Perturbation Recovery Rate)**

```
PRR_mode = Count(Hit and recover in mode) / Count(Hit in mode)
```

`Hit` = the run actually touched a perturbed tool call
(`metadata.perturbation_status == "perturbed"` in the saved trace).

**RC (Recovery Cost)**

```
For each run r in mode:
  RC_r = 0,                                   if r does not hit the perturbation
  RC_r = 1,                                   if r hits but fails to recover
  RC_r = 1 - C_oracle(r) / max(C_act, C_oracle), if r hits and recovers

RC_mode = mean(RC_r over runs in mode)
```

- `C_act` — number of tool-call results from the first perturbed hit to end of run.
- `C_oracle` — minimum recovery suffix cost derived from the task structure.
- `RC ∈ [0, 1]`. No-hit runs contribute 0, hit-and-fail runs contribute 1.

## How Perturbation Injection Works

`evaluation/core/sandbox.py` wraps the tool runtime with an
`ExecutionEngine`:

- C1: a single perturbation point per task.
- C2 / C3: per-path perturbation maps, activated via *first-touch* on an
  alternative tool.
- C4: per-slot first-touch — each slot's first-called tool becomes the
  victim for that slot.
- P1 / P3: transient perturbation (only the first call to the victim
  returns the corrupted output).
- P2 / P4: persistent perturbation (every call returns corrupted output).

The trace logger records every round, tool call, perturbation status, and
token count so the judge can score recovery behaviour.

## Adding a new agent backend

Implement `evaluation/agents/<name>_agent.py` exposing a class that
inherits `BaseAgent` (see `base_agent.py`), then register it in
`evaluation/agents/__init__.py` and add a branch in
`evaluation/scripts/run_eval.py:create_agent()`.

## Citation
```bibtex
@misc{zhu2026toolsfailbenchmarkingdynamic,
      title={When Tools Fail: Benchmarking Dynamic Replanning and Anomaly Recovery in LLM Agents}, 
      author={Dongsheng Zhu and Xuchen Ma and Yucheng Shen and Xiang Li and Yukun Zhao and Shuaiqiang Wang and Lingyong Yan and Dawei Yin},
      year={2026},
      eprint={2606.05806},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2606.05806}, 
}
```
