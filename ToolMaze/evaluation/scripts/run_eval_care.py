"""
ToolMaze/evaluation/scripts/run_eval_care.py
Evaluation runner for CARE (7-Layer Orchestration) vs Baseline.

Supports:
- Multi-key rotation across 6+ Gemini API keys with thread-safe rate-limit recovery
- Seamless local fallback to Ollama (qwen3:8b) or vLLM if API limits are reached
- Automatic evaluation across C1, C2, C3, C4 tasks under P0, P1, P2, P3, P4
- Comprehensive TSR, PRR, and RC metric calculation and reporting
"""

import argparse
import json
import logging
import os
import sys
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
from openai import OpenAI

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.core import ExecutionEngine, JudgeSystem, MetricsCalculator
from evaluation.utils import ResultSaver
from evaluation.agents import BaseAgent, OpenAIAgent, CAREAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CARE_Eval")

DEFAULT_TASK_DIRS = {
    "c1": "data/perturbed_tasks/c1",
    "c2": "data/perturbed_tasks/c2",
    "c3": "data/perturbed_tasks/c3",
    "c4": "data/perturbed_tasks/c4",
}


# =========================================================================
# Multi-Key Rotation Pool
# =========================================================================
class SharedKeyPool:
    def __init__(self, api_keys: List[str], base_url: str, delay_seconds: float = 0.5):
        self.api_keys = [k.strip() for k in api_keys if k and k.strip()]
        if not self.api_keys:
            self.api_keys = ["dummy_key"]
        self.clients = [OpenAI(api_key=k, base_url=base_url) for k in self.api_keys]
        self.lock = threading.Lock()
        self.index = 0
        self.delay_seconds = delay_seconds
        self.next_request_time = 0.0
        logger.info(f"Initialized SharedKeyPool with {len(self.clients)} keys at {base_url}.")

    def get_client_and_wait(self):
        with self.lock:
            now = time.monotonic()
            if now < self.next_request_time:
                time.sleep(self.next_request_time - now)
            client = self.clients[self.index]
            cur_idx = self.index
            self.index = (self.index + 1) % len(self.clients)
            self.next_request_time = time.monotonic() + self.delay_seconds
            return client, cur_idx


class RotatingCompletions:
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
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    sleep_time = min(2 ** attempt + 1, 15)
                    logger.warning(f"[Key #{key_idx+1}] Rate limit hit (429). Rotating to next key. Sleeping {sleep_time}s...")
                    time.sleep(sleep_time)
                    continue
                elif "401" in err_str or "403" in err_str or "404" in err_str or "not found" in err_str:
                    logger.warning(f"[Key #{key_idx+1}] Key error / Model not enabled (401/403/404). Rotating to next key immediately...")
                    continue
                raise
        raise Exception(f"Max retries exceeded across all keys. Last error: {last_error}")


class RotatingChat:
    def __init__(self, pool: SharedKeyPool):
        self.completions = RotatingCompletions(pool)


class RotatingOpenAIClient:
    def __init__(self, pool: SharedKeyPool):
        self.chat = RotatingChat(pool)


# =========================================================================
# Key Extraction Helper
# =========================================================================
def extract_keys_from_env_file(filepath: Path) -> List[str]:
    """Parse environment file and extract all Gemini / Google API keys."""
    keys = []
    if not filepath.exists():
        return keys
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if line.startswith("export "):
                    line = line[len("export "):].strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip().upper()
                    v = v.strip().strip('"').strip("'")
                    if ("GEMINI" in k or "GOOGLE" in k) and v and len(v) > 10:
                        keys.append(v)
    except Exception as e:
        logger.warning(f"Error reading {filepath}: {e}")
    return keys


def gather_all_keys(custom_env_file: Optional[str] = None) -> List[str]:
    """Gather all available API keys from env vars and known env files."""
    keys = []
    # 1. Environment variables
    for k, v in os.environ.items():
        if ("GEMINI_API_KEY" in k or "GOOGLE_API_KEY" in k) and v:
            keys.append(v)

    # 2. Custom env file if specified
    if custom_env_file:
        keys.extend(extract_keys_from_env_file(Path(custom_env_file)))

    # 3. Known default server locations
    default_locations = [
        Path("/mnt/data/toolmaze_project/secrets/gemini_env"),
        Path("/mnt/data/toolmaze_project/ToolMaze/gemini_env"),
        project_root / ".env",
        project_root.parent / ".env"
    ]
    for loc in default_locations:
        if loc.exists():
            keys.extend(extract_keys_from_env_file(loc))

    # Deduplicate while preserving order
    seen = set()
    unique_keys = []
    for k in keys:
        if k not in seen and len(k) > 10:
            seen.add(k)
            unique_keys.append(k)

    return unique_keys


# =========================================================================
# Task & Config Loaders
# =========================================================================
def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
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


def load_tasks(task_dir: str, modes=None, task_id=None, offset=0, limit=None):
    task_dir_path = Path(task_dir)
    tasks = []
    if task_id:
        task_file = task_dir_path / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, "r", encoding="utf-8") as f:
                tasks.append(json.load(f))
        return tasks

    for task_file in sorted(task_dir_path.glob("*.json")):
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task = json.load(f)
                if modes and task.get("perturbation_mode", "P0") not in modes:
                    continue
                tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to load {task_file}: {e}")

    if offset or limit is not None:
        tasks = tasks[offset: (offset + limit) if limit is not None else None]
    return tasks


def create_eval_agent(agent_type: str, config: Dict[str, Any], shared_pool: Optional[SharedKeyPool] = None) -> BaseAgent:
    """Create either CAREAgent or baseline OpenAIAgent."""
    agent_config = config["agent"]
    model = agent_config.get("model", "gemma-4-31b-it")
    base_url = agent_config.get("base_url")
    temp = agent_config.get("temperature", 0.0)
    max_tokens = agent_config.get("max_tokens", 4096)

    # Underlying OpenAIAgent
    base_llm = OpenAIAgent(
        model=model,
        api_key="dummy_key",
        base_url=base_url,
        temperature=temp,
        max_tokens=max_tokens
    )
    if shared_pool:
        base_llm.client = RotatingOpenAIClient(shared_pool)

    if agent_type == "care":
        tools_dir = config["data"].get("tools_dir")
        return CAREAgent(
            base_agent=base_llm,
            model=model,
            enable_sov=True,
            enable_care_recovery=True,
            tools_dir=tools_dir
        )
    else:
        return base_llm


def evaluate_single_task(task_json, config, tools_dir, judge, saver, shared_pool, agent_type="care"):
    task_id = task_json["task_id"]
    mode = task_json.get("perturbation_mode", "P0")

    eval_file = saver.evaluations_dir / f"{task_id}_{mode}_eval.json"
    inf_file = saver.inferences_dir / f"{task_id}_{mode}_inference.json"
    if eval_file.exists() and inf_file.exists() and config.get("resume", True):
        try:
            with open(eval_file, "r", encoding="utf-8") as f:
                judgement = json.load(f)
            with open(inf_file, "r", encoding="utf-8") as f:
                inf_data = json.load(f)
            logger.info(f"[{agent_type.upper()}] Reusing existing result for {task_id} (Mode: {mode}) -> {'PASS' if judgement.get('pass') else 'FAIL'}")
            return {
                "task_id": task_id,
                "mode": mode,
                "passed": judgement.get("pass", False),
                "judgement": judgement,
                "task_json": task_json,
                "inference_data": inf_data
            }
        except Exception as e:
            logger.warning(f"Failed to read existing cache for {task_id}_{mode}: {e}")

    logger.info(f"[{agent_type.upper()}] Starting {task_id} (Mode: {mode})")

    try:
        agent = create_eval_agent(agent_type, config, shared_pool)
        if hasattr(agent, "set_task_json"):
            agent.set_task_json(task_json)

        val_cfg = {"enabled": True, "fail_fast": False}
        engine = ExecutionEngine(
            task_json=task_json,
            agent=agent,
            tools_dir=tools_dir,
            validation_config=val_cfg
        )
        trace_logger, token_usage = engine.run(max_rounds=config["execution"]["max_rounds"])
        inference_data = trace_logger.to_dict(token_usage=token_usage)
        saver.save_inference(task_id, mode, trace_logger, token_usage)

        if judge is None:
            return {"task_id": task_id, "mode": mode, "passed": None, "task_json": task_json, "inference_data": inference_data}

        judgement = judge.judge(task_json, inference_data)
        saver.save_evaluation(task_id, mode, judgement)
        logger.info(f"  ✓ {task_id} Result: {'PASS' if judgement['pass'] else 'FAIL'}")

        return {
            "task_id": task_id,
            "mode": mode,
            "passed": judgement["pass"],
            "judgement": judgement,
            "task_json": task_json,
            "inference_data": inference_data
        }
    except Exception as e:
        logger.error(f"  ✗ {task_id} Error: {e}", exc_info=False)
        return {"task_id": task_id, "mode": mode, "passed": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Evaluate ToolMaze with CARE Architecture")
    parser.add_argument("--config", type=str, default="evaluation/configs/gemini_eval_config_c1.yaml")
    parser.add_argument("--agent-type", type=str, default="care", choices=["care", "baseline"])
    parser.add_argument("--backend", type=str, default="gemini", choices=["gemini", "ollama", "vllm"])
    parser.add_argument("--category", type=str, default=None, choices=["c1", "c2", "c3", "c4"])
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--ollama-url", type=str, default="http://localhost:11434/v1")
    parser.add_argument("--env-file", type=str, default=None)
    parser.add_argument("--modes", nargs="+", default=None)
    parser.add_argument("--task-id", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--max-workers", type=int, default=2)
    parser.add_argument("--no-resume", action="store_true", default=False, help="Disable caching and re-run all tasks")
    args, _ = parser.parse_known_args()

    config = load_config(args.config)
    config["resume"] = not args.no_resume
    if args.category:
        config["data"]["task_category"] = args.category
        if args.category in DEFAULT_TASK_DIRS:
            config["data"]["task_dir"] = DEFAULT_TASK_DIRS[args.category]
    if args.modes:
        expanded_modes = []
        for m in args.modes:
            expanded_modes.extend([x.strip() for x in m.split(",") if x.strip()])
        config["evaluation"]["modes"] = expanded_modes
    if args.model:
        config["agent"]["model"] = args.model
        config["judge"]["model"] = args.model

    # Configure backend endpoint
    if args.backend == "ollama":
        config["agent"]["base_url"] = args.ollama_url
        config["judge"]["base_url"] = args.ollama_url
        if not args.model:
            config["agent"]["model"] = "qwen3:8b"
            config["judge"]["model"] = "qwen3:8b"
        keys = ["ollama"]
    elif args.backend == "vllm":
        config["agent"]["base_url"] = "http://localhost:8000/v1"
        config["judge"]["base_url"] = "http://localhost:8000/v1"
        keys = ["EMPTY"]
    else:  # Gemini
        keys = gather_all_keys(args.env_file)
        if not keys:
            logger.warning("No Gemini API keys detected! Checking config key.")
            keys = [config["agent"].get("api_key", "dummy")]
        logger.info(f"Loaded {len(keys)} Gemini API keys for rotation.")

    shared_pool = SharedKeyPool(keys, config["agent"]["base_url"], delay_seconds=1.0)
    tools_dir = config["data"]["tools_dir"]

    judge_client = RotatingOpenAIClient(shared_pool)
    judge = JudgeSystem(
        llm_client=judge_client,
        model=config["judge"]["model"],
        template_dir=config["data"].get("template_dir")
    )
    metrics = MetricsCalculator()

    category = config["data"].get("task_category", "c1")
    saver = ResultSaver(
        base_dir=config["data"]["output_dir"],
        model=f"{config['agent']['model']}-{args.agent_type}",
        agent_type="care" if args.agent_type == "care" else "fc",
        task_category=category
    )

    tasks = load_tasks(
        config["data"]["task_dir"],
        modes=config["evaluation"]["modes"],
        task_id=args.task_id,
        offset=args.offset,
        limit=args.limit
    )
    logger.info(f"Loaded {len(tasks)} tasks from {config['data']['task_dir']}")

    max_workers = args.max_workers
    logger.info(f"Running evaluation with {max_workers} worker threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(evaluate_single_task, task, config, tools_dir, judge, saver, shared_pool, args.agent_type)
            for task in tasks
        ]
        for future in as_completed(futures):
            res = future.result()
            if "error" not in res and res.get("judgement"):
                metrics.add_result(res["task_json"], res["inference_data"], res["judgement"])

    report = metrics.generate_report()
    saver.save_metrics(report)
    print("\n" + "=" * 60)
    print(f"EVALUATION COMPLETE: [{args.agent_type.upper()}] on Category {category.upper()}")
    print("=" * 60)
    print(metrics.print_summary(report))


if __name__ == "__main__":
    main()
