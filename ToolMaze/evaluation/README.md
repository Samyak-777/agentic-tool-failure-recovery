# TOOLMAZE Evaluation System

Complete evaluation framework for testing LLM agents on C1/C2/C3/C4 tasks with P0-P4 perturbation modes.

> The full project README lives at the ToolMaze project root
> (`../README.md`). This file documents the `evaluation/` sub-package only.

## Quick Start

### 1. Install Dependencies

```bash
# Activate your conda environment
conda activate toolmaze

# Install dependencies (top-level)
pip install -r ../requirements.txt
```

### 2. Configure

Edit `evaluation/configs/openai_eval_config_c1.yaml`:

```yaml
agent:
  type: "openai"  # or "anthropic", "vllm"
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"

judge:
  model: "gpt-5.5"
  api_key: "${OPENAI_API_KEY}"
```

Set environment variables:

```bash
export OPENAI_API_KEY="your-key"
```

### 3. Run Evaluation

**specific task eval:**

```bash
# Run single task (for testing) - use new task ID format
python evaluation/scripts/run_eval.py --task-id C1_task_001_P0

# Run all P0 tasks
python evaluation/scripts/run_eval.py --modes P0

# Run C3 tasks
python evaluation/scripts/run_eval.py --task-category c3 --modes P0 P1 P2 P3 P4

# Run C4 tasks
python evaluation/scripts/run_eval.py --task-category c4 --modes P0 P1 P2 P3 P4

# Run full evaluation (all modes)
python evaluation/scripts/run_eval.py --modes P0 P1 P2 P3 P4

# Run with specific agent/model
python evaluation/scripts/run_eval.py --agent-type openai --model gpt-4o --modes P0 P1
```

**batch eval for multiple models:**

Config your models and coworkers in run_batch_api_eval.py (all models use same url and api-key, config at `evaluation/configs/openai_eval_config_c1.yaml`).

```python
MODELS: dict[str, int] = {
    "gpt-5.5": 4,
    "gemini-3.1-pro-preview": 4,
    "deepseek-v4-pro": 4,
    "kimi-k2.6": 2,
    "glm-5.1": 4,
    "qwen3.6-27b": 4,
    "MiniMax-M2.7": 4,
    "qwen3.5-35b-a3b": 4,
    "qwen3.5-397b-a17b": 4,
    "claude-sonnet-4-6": 2,
}
```

Run `run_batch_api_eval.py`.

```bash
# full evaluation (C1-C4, P0-P4, w/ hint, w/o hint)
python run_batch_api_eval.py

# set special categories
python run_batch_api_eval.py --categories c3 c4

# set special modes
python run_batch_api_eval.py --modes P2 P4
```

## Architecture

```
evaluation/
├── core/
│   ├── sandbox.py       # Execution engine with perturbation injection
│   ├── judge.py         # Complexity-specific judgement logic
│   └── metrics.py       # TSR / FRR / RC aggregation
├── agents/
│   ├── openai_agent.py  # OpenAI/GPT support
│   ├── anthropic_agent.py  # Claude support
│   └── vllm_agent.py    # VLLM deployed models
├── utils/
│   ├── trace_logger.py  # Inference trace recording
│   └── result_saver.py  # Result persistence
├── scripts/
│   ├── run_eval.py      # Main evaluation script
│   └── batch_eval.sh    # Batch runner
└── results/{model}/{fc|mcp}/{c1|c2|c3|c4}/
    ├── inferences/      # Saved model traces
    ├── evaluations/     # Judge outputs
    ├── metrics/         # Aggregated TSR / FRR / RC reports
    └── reports/         # Optional text reports
```

## Output Files

All outputs are saved under:

```
evaluation/results/{MODEL_NAME}/{fc}/{c1|c2|c3|c4}/
```

### Inference Trace

```
inferences/{task_id}_{mode}_inference.json
```

- Full message trace in chat format
- Tool-call metadata and perturbation status
- Token usage in `tokens`

### Evaluation Result

```
evaluations/{task_id}_{mode}_eval.json
```

- `pass` / `failure_reason`
- `trace_check`
- Complexity-specific fields such as `victim_tool`, `matched_paths`, and `switched_paths`

### Metrics Report

```
metrics/metrics_report_{timestamp}.json
```

- `tsr`
- `prr`
- `rc`
- `mode_breakdown`
- `recovery_breakdown`
- `insights`

## Metrics Reference

**TSR (Task Success Rate)**

```text
TSR_mode = Count(Pass runs in mode) / Total runs in mode
```

**PRR (Perturbation Recovery Rate)**

```text
FRR_mode = Count(Hit and recover in mode) / Count(Hit in mode)
```

`Hit` means the run actually touched a perturbed tool call, identified from the saved inference trace via `metadata.perturbation_status == "perturbed"`.

**RC (Recovery Cost)**

```text
For each run r in mode:
  RC_r = 0, if r does not hit the perturbation
  RC_r = 1, if r hits the perturbation but fails
  RC_r = 1 - C_oracle(r) / max(C_act(r), C_oracle(r)), if r hits and passes

RC_mode = mean(RC_r | runs in mode)
```

Where:

- `C_act` is the number of tool-call results from the first perturbed hit to the end of the run.
- `C_oracle` is the task-derived minimum recovery suffix cost, computed from the task structure rather than copied from a P0 run.
- RC stays in `[0, 1]` for every run.
- `no-hit` samples contribute `0` because no recovery work was incurred.
- `hit-and-fail` samples contribute `1` because the run paid recovery cost but still failed to recover.