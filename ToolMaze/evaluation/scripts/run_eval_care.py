"""CARE Architecture Full Evaluation Script.

Runs the 7-layer CARE (Cost-Aware Recovery Engine) agent against ToolMaze
benchmark tasks and compares results against the baseline (raw OpenAI agent).

Supports:
- Multi-key rotation for Gemini API (SharedKeyPool)
- All task categories (C1–C4) and perturbation modes (P0–P4)
- Parallel execution with configurable worker count
- Resume from interrupted runs (skip already-completed inferences)
- Side-by-side comparison against baseline results

Usage:
    # Run CARE evaluation on C1 tasks
    python evaluation/scripts/run_eval_care.py --config evaluation/configs/gemini_eval_config_c1.yaml

    # Run specific modes
    python evaluation/scripts/run_eval_care.py --config evaluation/configs/gemini_eval_config_c1.yaml --modes P0 P1

    # Run a single task
    python evaluation/scripts/run_eval_care.py --config evaluation/configs/gemini_eval_config_c1.yaml --task-id C1_task_001_P1

    # Run with limit
    python evaluation/scripts/run_eval_care.py --config evaluation/configs/gemini_eval_config_c1.yaml --limit 10

    # Disable CARE layers (baseline mode for comparison)
    python evaluation/scripts/run_eval_care.py --config evaluation/configs/gemini_eval_config_c1.yaml --baseline
"""

import argparse
import json
import logging
import os
import sys
import time
import threading
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.core import ExecutionEngine, JudgeSystem, MetricsCalculator
from evaluation.utils import ResultSaver
from openai import OpenAI

# --------------------
# Logging Setup
# --------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('care_evaluation.log', mode='a')
    ]
)
logger = logging.getLogger("CARE_EVAL")

DEFAULT_TASK_DIRS = {
    "c1": "data/perturbed_tasks/c1",
    "c2": "data/perturbed_tasks/c2",
    "c3": "data/perturbed_tasks/c3",
    "c4": "data/perturbed_tasks/c4",
}


# ==========================================
# MULTI-KEY ROTATION LOGIC (THREAD-SAFE)
# ==========================================
class SharedKeyPool:
    """Thread-safe round-robin API key pool with rate limiting."""

    def __init__(self, api_keys: List[str], base_url: str, delay_seconds: float = 1.5):
        self.clients = [OpenAI(api_key=k, base_url=base_url) for k in api_keys if k.strip()]
        self.lock = threading.Lock()
        self.index = 0
        self.delay_seconds = delay_seconds
        self.next_request_time = 0.0
        self.error_counts = {i: 0 for i in range(len(self.clients))}
        logger.info(f"SharedKeyPool initialized with {len(self.clients)} API keys, delay={delay_seconds}s")

    def get_client_and_wait(self) -> Tuple:
        with self.lock:
            now = time.monotonic()
            if now < self.next_request_time:
                time.sleep(self.next_request_time - now)
            client = self.clients[self.index]
            idx = self.index
            self.index = (self.index + 1) % len(self.clients)
            self.next_request_time = time.monotonic() + self.delay_seconds
            return client, idx

    def report_error(self, key_idx: int):
        with self.lock:
            self.error_counts[key_idx] = self.error_counts.get(key_idx, 0) + 1


class RotatingCompletions:
    """Retry-aware completion wrapper with exponential backoff."""

    def __init__(self, pool: SharedKeyPool, max_retries: int = 8):
        self.pool = pool
        self.max_retries = max_retries

    def create(self, *args, **kwargs):
        last_error = None
        for attempt in range(self.max_retries):
            client, key_idx = self.pool.get_client_and_wait()
            try:
                return client.chat.completions.create(*args, **kwargs)
            except Exception as e:
                last_error = e
                err_str = str(e).lower()
                self.pool.report_error(key_idx)

                if "429" in err_str or "resource_exhausted" in err_str or "too many requests" in err_str:
                    sleep_time = min(2 ** attempt + 1, 60)
                    logger.warning(f"[Key {key_idx}] Rate limit. Retry in {sleep_time}s (attempt {attempt+1}/{self.max_retries})")
                    time.sleep(sleep_time)
                    continue
                elif "403" in err_str or "401" in err_str:
                    logger.warning(f"[Key {key_idx}] Auth error. Rotating key...")
                    continue
                elif "500" in err_str or "503" in err_str or "server" in err_str:
                    sleep_time = min(2 ** attempt, 30)
                    logger.warning(f"[Key {key_idx}] Server error. Retry in {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                else:
                    raise
        raise Exception(f"Max retries ({self.max_retries}) exceeded. Last error: {last_error}")


class RotatingChat:
    def __init__(self, pool: SharedKeyPool):
        self.completions = RotatingCompletions(pool)


class RotatingOpenAIClient:
    def __init__(self, pool: SharedKeyPool):
        self.chat = RotatingChat(pool)


# ==========================================
# CONFIGURATION & TASK LOADING
# ==========================================
def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    def expand_env(obj):
        if isinstance(obj, dict):
            return {k: expand_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [expand_env(v) for v in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            return os.environ.get(obj[2:-1], obj)
        return obj

    return expand_env(config)


def load_env_file(env_path: str) -> None:
    """Load environment variables from a file (KEY=VALUE format)."""
    if not os.path.exists(env_path):
        logger.warning(f"Env file not found: {env_path}")
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip()
    logger.info(f"Loaded env vars from {env_path}")


def load_tasks(task_dir: str, modes=None, task_id=None, offset=0, limit=None) -> List[Dict]:
    task_dir = Path(task_dir)
    tasks = []

    if task_id:
        task_file = task_dir / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r') as f:
                tasks.append(json.load(f))
        else:
            logger.error(f"Task file not found: {task_file}")
        return tasks

    for task_file in sorted(task_dir.glob("*.json")):
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
                if modes and task.get("perturbation_mode", "P0") not in modes:
                    continue
                tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to load {task_file}: {e}")

    if offset or limit is not None:
        tasks = tasks[offset: (offset + limit) if limit is not None else None]

    return tasks


def infer_task_category(task_dir: Optional[str] = None, task_id: Optional[str] = None) -> Optional[str]:
    if task_id:
        tid_upper = task_id.upper()
        for cat in ["C1", "C2", "C3", "C4"]:
            if tid_upper.startswith(f"{cat}_"):
                return cat.lower()
    if task_dir:
        normalized = task_dir.replace("\\", "/").rstrip("/").lower()
        for cat in ["c1", "c2", "c3", "c4"]:
            if normalized.endswith(f"/{cat}"):
                return cat
    return None


# ==========================================
# AGENT CREATION
# ==========================================
def create_care_agent(config: Dict[str, Any], task_json: Dict[str, Any], shared_pool: SharedKeyPool):
    """Create a CAREAgent wrapping an OpenAI-compatible base agent."""
    from evaluation.agents import OpenAIAgent, CAREAgent
    from tool_memory import BudgetConfig

    agent_config = config["agent"]

    # Create base OpenAI agent
    base_agent = OpenAIAgent(
        model=agent_config["model"],
        api_key=agent_config.get("api_key", "dummy"),
        base_url=agent_config.get("base_url"),
        temperature=agent_config.get("temperature", 1.0),
        max_tokens=agent_config.get("max_tokens", 10240)
    )

    # Inject rotating client for multi-key support
    if shared_pool:
        base_agent.client = RotatingOpenAIClient(shared_pool)

    # Configure CARE budget
    budget_config = BudgetConfig(
        max_recovery_tool_calls=8,
        max_retries_per_tool=2
    )

    # Create CAREAgent wrapping the base agent
    care_agent = CAREAgent(
        base_agent=base_agent,
        budget_config=budget_config,
        enable_sov=True,
        enable_care_recovery=True
    )

    # Pre-set task_json so CARE layers have access to task metadata
    care_agent.task_json = task_json

    if agent_config.get("force_p0_prompt") and hasattr(base_agent, "force_p0_prompt"):
        base_agent.force_p0_prompt = True

    return care_agent


def create_baseline_agent(config: Dict[str, Any], shared_pool: SharedKeyPool):
    """Create a baseline OpenAI agent (no CARE layers)."""
    from evaluation.agents import OpenAIAgent

    agent_config = config["agent"]
    agent = OpenAIAgent(
        model=agent_config["model"],
        api_key=agent_config.get("api_key", "dummy"),
        base_url=agent_config.get("base_url"),
        temperature=agent_config.get("temperature", 1.0),
        max_tokens=agent_config.get("max_tokens", 10240)
    )

    if shared_pool:
        agent.client = RotatingOpenAIClient(shared_pool)

    if agent_config.get("force_p0_prompt") and hasattr(agent, "force_p0_prompt"):
        agent.force_p0_prompt = True

    return agent


# ==========================================
# SINGLE TASK EVALUATION
# ==========================================
def evaluate_single_task(
    task_json: Dict[str, Any],
    config: Dict[str, Any],
    tools_dir: str,
    judge: JudgeSystem,
    saver: ResultSaver,
    shared_pool: SharedKeyPool,
    is_baseline: bool = False
) -> Dict[str, Any]:
    """Evaluate a single task with CARE or baseline agent."""
    task_id = task_json["task_id"]
    mode = task_json.get("perturbation_mode", "P0")
    agent_label = "BASELINE" if is_baseline else "CARE"

    logger.info(f"[{agent_label}] Processing {task_id} (Mode: {mode})")

    try:
        # Check if already computed
        if saver.inference_exists(task_id, mode):
            logger.info(f"  ✓ {task_id} Inference exists, loading from disk")
            inference_data = saver.load_inference(task_id, mode)
            tokens = inference_data.get("tokens", {})
            legacy = inference_data.get("token_usage", {})
            token_usage = {
                "input_tokens": tokens.get("input_tokens", legacy.get("prompt_tokens", 0)),
                "output_tokens": tokens.get("output_tokens", legacy.get("completion_tokens", 0)),
                "total_tokens": tokens.get("total_tokens", legacy.get("total_tokens", 0))
            }
        else:
            logger.info(f"  → {task_id} Running {agent_label} inference...")

            if is_baseline:
                agent = create_baseline_agent(config, shared_pool)
            else:
                agent = create_care_agent(config, task_json, shared_pool)

            engine = ExecutionEngine(task_json, agent, tools_dir=tools_dir)
            trace_logger, token_usage = engine.run(max_rounds=config["execution"]["max_rounds"])
            inference_data = trace_logger.to_dict(token_usage=token_usage)
            saver.save_inference(task_id, mode, trace_logger, token_usage)
            logger.info(f"  ✓ {task_id} Inference saved | Tokens: {token_usage.get('total_tokens', 'N/A')}")

        # Run judge evaluation
        if judge is None:
            return {
                "task_id": task_id,
                "mode": mode,
                "passed": None,
                "task_json": task_json,
                "inference_data": inference_data,
                "agent_type": agent_label
            }

        logger.info(f"  → {task_id} Running evaluation...")
        judgement = judge.judge(task_json, inference_data)
        saver.save_evaluation(task_id, mode, judgement)
        passed = judgement.get("pass", False)
        logger.info(f"  ✓ {task_id} Result: {'PASS' if passed else 'FAIL'}")

        return {
            "task_id": task_id,
            "mode": mode,
            "passed": passed,
            "judgement": judgement,
            "task_json": task_json,
            "inference_data": inference_data,
            "agent_type": agent_label
        }

    except Exception as e:
        logger.error(f"  ✗ {task_id} Error: {e}")
        logger.debug(traceback.format_exc())
        return {
            "task_id": task_id,
            "mode": mode,
            "passed": False,
            "error": str(e),
            "agent_type": agent_label
        }


# ==========================================
# MAIN EVALUATION PIPELINE
# ==========================================
def main():
    parser = argparse.ArgumentParser(description="CARE Architecture ToolMaze Evaluation")
    parser.add_argument("--config", type=str, default="evaluation/configs/gemini_eval_config_c1.yaml",
                        help="Path to evaluation config YAML")
    parser.add_argument("--env-file", type=str, default="evaluation/configs/env",
                        help="Path to env file with API keys")
    parser.add_argument("--modes", nargs="+", default=None,
                        help="Perturbation modes to evaluate (e.g., P0 P1 P2 P3 P4)")
    parser.add_argument("--task-id", type=str, default=None,
                        help="Run a single task by ID")
    parser.add_argument("--task-category", type=str, default=None,
                        choices=["c1", "c2", "c3", "c4"],
                        help="Override task category")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of tasks to process")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip first N tasks")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of parallel workers")
    parser.add_argument("--baseline", action="store_true",
                        help="Run baseline (no CARE layers) for comparison")
    parser.add_argument("--delay", type=float, default=1.5,
                        help="Delay between API calls (seconds)")
    parser.add_argument("--skip-judge", action="store_true",
                        help="Skip judge evaluation (inference only)")
    args = parser.parse_args()

    # Load env file (API keys)
    load_env_file(args.env_file)

    # Load config
    config = load_config(args.config)

    # Override config with CLI args
    if args.modes:
        config["evaluation"]["modes"] = args.modes
    if args.task_category:
        config["data"]["task_category"] = args.task_category
        config["data"]["task_dir"] = DEFAULT_TASK_DIRS.get(args.task_category, config["data"]["task_dir"])
    if args.workers:
        config["evaluation"]["max_workers"] = args.workers

    # Infer category
    category = args.task_category or infer_task_category(
        task_dir=config["data"].get("task_dir"),
        task_id=args.task_id
    ) or config["data"].get("task_category", "c1")

    # Gather API keys from environment
    api_keys = sorted([v for k, v in os.environ.items() if k.startswith("GEMINI_API_KEY")])
    if not api_keys:
        logger.warning("No GEMINI_API_KEY_* env vars found. Using config key.")
        api_keys = [config["agent"].get("api_key")]

    logger.info(f"API Keys available: {len(api_keys)}")
    logger.info(f"Task category: {category}")
    logger.info(f"Mode: {'BASELINE' if args.baseline else 'CARE'}")

    # Create shared key pool
    base_url = config["agent"].get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai")
    shared_pool = SharedKeyPool(api_keys, base_url, delay_seconds=args.delay)

    # Setup judge
    judge = None
    if not args.skip_judge:
        judge_client = RotatingOpenAIClient(shared_pool)
        judge = JudgeSystem(
            llm_client=judge_client,
            model=config["judge"]["model"],
            template_dir=config["data"].get("template_dir")
        )

    # Setup metrics calculator
    metrics = MetricsCalculator()

    # Setup result saver (different output dir for CARE vs baseline)
    agent_type_label = "fc" if args.baseline else "care"
    saver = ResultSaver(
        base_dir=config["data"]["output_dir"],
        model=config["agent"]["model"],
        agent_type=agent_type_label,
        task_category=category
    )

    # Load tasks
    tools_dir = config["data"]["tools_dir"]
    tasks = load_tasks(
        config["data"]["task_dir"],
        modes=config["evaluation"].get("modes"),
        task_id=args.task_id,
        offset=args.offset,
        limit=args.limit
    )

    logger.info(f"Loaded {len(tasks)} tasks from {config['data']['task_dir']}")
    if not tasks:
        logger.error("No tasks found! Check task_dir and modes.")
        return

    max_workers = config["evaluation"].get("max_workers", 4)
    logger.info(f"Running with {max_workers} parallel workers")

    # ---- Execute evaluation ----
    results = []
    completed = 0
    failed = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                evaluate_single_task,
                task, config, tools_dir, judge, saver, shared_pool,
                is_baseline=args.baseline
            ): task["task_id"]
            for task in tasks
        }

        for future in as_completed(futures):
            task_id = futures[future]
            try:
                res = future.result()
                results.append(res)
                completed += 1

                if "error" not in res and res.get("judgement"):
                    metrics.add_result(res["task_json"], res["inference_data"], res["judgement"])

                if completed % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = completed / elapsed if elapsed > 0 else 0
                    logger.info(f"Progress: {completed}/{len(tasks)} tasks ({rate:.1f} tasks/s)")

            except Exception as e:
                failed += 1
                logger.error(f"Task {task_id} future failed: {e}")

    # ---- Generate report ----
    elapsed_total = time.time() - start_time
    report = metrics.generate_report()
    saver.save_metrics(report)

    # Print summary
    summary = metrics.print_summary(report)
    print("\n" + "=" * 70)
    print(f"CARE EVALUATION COMPLETE ({'BASELINE' if args.baseline else 'CARE ARCHITECTURE'})")
    print("=" * 70)
    print(f"Category: {category.upper()}")
    print(f"Tasks: {completed}/{len(tasks)} completed, {failed} failed")
    print(f"Time: {elapsed_total:.1f}s ({elapsed_total/60:.1f}m)")
    print(f"API Keys Used: {len(api_keys)}")
    print("-" * 70)
    print(summary)
    print("=" * 70)

    # Save a summary JSON for easy comparison
    summary_path = Path(config["data"]["output_dir"]) / config["agent"]["model"] / agent_type_label / category / "care_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_data = {
        "agent_type": "CARE" if not args.baseline else "BASELINE",
        "category": category,
        "model": config["agent"]["model"],
        "total_tasks": len(tasks),
        "completed": completed,
        "failed": failed,
        "elapsed_seconds": elapsed_total,
        "report": report,
        "api_keys_count": len(api_keys)
    }
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
