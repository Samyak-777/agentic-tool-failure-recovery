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

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.core import ExecutionEngine, JudgeSystem, MetricsCalculator
from evaluation.utils import ResultSaver
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_TASK_DIRS = {
    "c1": "data/perturbed_tasks/c1", "c2": "data/perturbed_tasks/c2",
    "c3": "data/perturbed_tasks/c3", "c4": "data/perturbed_tasks/c4",
}

# ==========================================
# MULTI-KEY ROTATION LOGIC (THREAD-SAFE)
# ==========================================
class SharedKeyPool:
    def __init__(self, api_keys, base_url, delay_seconds=1.0):
        self.clients = [OpenAI(api_key=k, base_url=base_url) for k in api_keys if k.strip()]
        self.lock = threading.Lock()
        self.index = 0
        self.delay_seconds = delay_seconds
        self.next_request_time = 0.0
        logger.info(f"Initialized SharedKeyPool with {len(self.clients)} keys.")

    def get_client_and_wait(self):
        with self.lock:
            # Enforce global rate limit (delay between any requests across all threads)
            now = time.monotonic()
            if now < self.next_request_time:
                time.sleep(self.next_request_time - now)
            
            client = self.clients[self.index]
            self.index = (self.index + 1) % len(self.clients)
            self.next_request_time = time.monotonic() + self.delay_seconds
            return client, self.index

class RotatingCompletions:
    def __init__(self, pool, max_retries=6):
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
                
                # Handle Rate Limits (429)
                if "429" in err_str or "resource_exhausted" in err_str or "too many requests" in err_str:
                    sleep_time = min(2 ** attempt, 30)
                    logger.warning(f"[Key {key_idx}] Rate limit hit. Retrying in {sleep_time}s... (Attempt {attempt+1}/{self.max_retries})")
                    time.sleep(sleep_time)
                    continue
                
                # Handle Bad Keys/Permissions (403/401)
                if "403" in err_str or "401" in err_str:
                    logger.warning(f"[Key {key_idx}] Auth/Permission error (403/401). Rotating to next key immediately...")
                    continue # Try the next key without sleeping
                
                raise # Re-raise if it's not a rate limit or auth error
                
        raise Exception(f"Max retries exceeded. Last error: {last_error}")

class RotatingChat:
    def __init__(self, pool):
        self.completions = RotatingCompletions(pool)

class RotatingOpenAIClient:
    def __init__(self, pool):
        self.chat = RotatingChat(pool)
# ==========================================

def infer_task_category_from_task_id(task_id: Optional[str]) -> Optional[str]:
    if not task_id: return None
    task_id_upper = task_id.upper()
    for cat in ["C1", "C2", "C3", "C4"]:
        if task_id_upper.startswith(f"{cat}_"): return cat.lower()
    return None

def infer_task_category_from_task_dir(task_dir: Optional[str]) -> Optional[str]:
    if not task_dir: return None
    normalized = task_dir.replace("\\", "/").rstrip("/").lower()
    for cat in ["c1", "c2", "c3", "c4"]:
        if normalized.endswith(f"/{cat}"): return cat
    return None

def apply_task_data_overrides(config: Dict[str, Any], args: argparse.Namespace) -> None:
    task_id_category = infer_task_category_from_task_id(args.task_id)
    if args.task_category and task_id_category and args.task_category != task_id_category:
        raise ValueError("Task category conflict")
    if args.task_dir: config["data"]["task_dir"] = args.task_dir
    if args.task_category:
        config["data"]["task_category"] = args.task_category
        if not args.task_dir: config["data"]["task_dir"] = DEFAULT_TASK_DIRS[args.task_category]
        return
    if args.task_dir:
        inferred = infer_task_category_from_task_dir(args.task_dir)
        if inferred: config["data"]["task_category"] = inferred
        return
    if task_id_category:
        config["data"]["task_category"] = task_id_category
        config["data"]["task_dir"] = DEFAULT_TASK_DIRS[task_id_category]

def load_config(config_path: str) -> Dict[str, Any]:
    with open(config_path, 'r') as f: config = yaml.safe_load(f)
    def expand_env(obj):
        if isinstance(obj, dict): return {k: expand_env(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [expand_env(v) for v in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            return os.environ.get(obj[2:-1], obj)
        return obj
    return expand_env(config)

def load_tasks(task_dir: str, modes=None, task_id=None, offset=0, limit=None):
    task_dir = Path(task_dir)
    tasks = []
    if task_id:
        task_file = task_dir / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r') as f: tasks.append(json.load(f))
        return tasks
    for task_file in sorted(task_dir.glob("*.json")):
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)
                if modes and task.get("perturbation_mode", "P0") not in modes: continue
                tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to load {task_file}: {e}")
    if offset or limit is not None:
        tasks = tasks[offset: (offset + limit) if limit is not None else None]
    return tasks

def create_agent(config: Dict[str, Any], shared_pool=None):
    agent_config = config["agent"]
    agent_type = agent_config["type"].lower()
    
    if agent_type == "openai":
        from evaluation.agents import OpenAIAgent
        agent = OpenAIAgent(
            model=agent_config["model"],
            api_key=agent_config.get("api_key", "dummy"),
            base_url=agent_config.get("base_url"),
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"]
        )
        # INJECT OUR SHARED ROTATING CLIENT HERE
        if shared_pool:
            agent.client = RotatingOpenAIClient(shared_pool)
    else:
        raise NotImplementedError("Only OpenAI-compatible agent supports multi-key right now.")

    if agent_config.get("force_p0_prompt") and hasattr(agent, "force_p0_prompt"):
        agent.force_p0_prompt = True
    return agent

def evaluate_single_task(task_json, config, tools_dir, judge, saver, shared_pool):
    task_id = task_json["task_id"]
    mode = task_json.get("perturbation_mode", "P0")
    logger.info(f"Processing {task_id} (Mode: {mode})")
    
    try:
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
            logger.info(f"  → {task_id} Running inference...")
            agent = create_agent(config, shared_pool)
            engine = ExecutionEngine(task_json, agent, tools_dir=tools_dir)
            trace_logger, token_usage = engine.run(max_rounds=config["execution"]["max_rounds"])
            inference_data = trace_logger.to_dict(token_usage=token_usage)
            saver.save_inference(task_id, mode, trace_logger, token_usage)
            logger.info(f"  ✓ {task_id} Inference saved | Tokens: {token_usage['total_tokens']}")

        if judge is None:
            return {"task_id": task_id, "mode": mode, "passed": None, "task_json": task_json, "inference_data": inference_data}

        logger.info(f"  → {task_id} Running evaluation...")
        judgement = judge.judge(task_json, inference_data)
        saver.save_evaluation(task_id, mode, judgement)
        logger.info(f"  ✓ {task_id} Result: {'PASS' if judgement['pass'] else 'FAIL'}")

        return {"task_id": task_id, "mode": mode, "passed": judgement["pass"], "judgement": judgement, "task_json": task_json, "inference_data": inference_data}

    except Exception as e:
        logger.error(f"  ✗ {task_id} Error: {e}", exc_info=False)
        return {"task_id": task_id, "mode": mode, "passed": False, "error": str(e)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="evaluation/configs/openai_eval_config_c1.yaml")
    parser.add_argument("--modes", nargs="+", default=None)
    parser.add_argument("--task-id", type=str, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    args, unknown = parser.parse_known_args()

    config = load_config(args.config)
    if args.modes: config["evaluation"]["modes"] = args.modes
    
    # 1. Gather all API keys from environment variables matching GEMINI_API_KEY
    api_keys = [v for k, v in os.environ.items() if k.startswith("GEMINI_API_KEY")]
    if not api_keys:
        logger.warning("No GEMINI_API_KEY_* environment variables found. Trying default key in config.")
        api_keys = [config["agent"].get("api_key")]
        
    shared_pool = SharedKeyPool(api_keys, config["agent"].get("base_url"), delay_seconds=1.0)
    
    tools_dir = config["data"]["tools_dir"]
    judge_client = RotatingOpenAIClient(shared_pool)
    judge = JudgeSystem(llm_client=judge_client, model=config["judge"]["model"], template_dir=config["data"].get("template_dir"))
    metrics = MetricsCalculator()

    saver = ResultSaver(
        base_dir=config["data"]["output_dir"],
        model=config["agent"]["model"],
        agent_type="fc",
        task_category=config["data"].get("task_category", "c1")
    )

    tasks = load_tasks(config["data"]["task_dir"], modes=config["evaluation"]["modes"], task_id=args.task_id, offset=args.offset, limit=args.limit)
    logger.info(f"Loaded {len(tasks)} tasks")

    max_workers = config["evaluation"].get("max_workers", 4)
    logger.info(f"Running in parallel with {max_workers} workers")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(evaluate_single_task, task, config, tools_dir, judge, saver, shared_pool) for task in tasks]
        for future in as_completed(futures):
            res = future.result()
            if "error" not in res and res.get("judgement"):
                metrics.add_result(res["task_json"], res["inference_data"], res["judgement"])

    report = metrics.generate_report()
    saver.save_metrics(report)
    print("\n" + metrics.print_summary(report))
    logger.info("Evaluation completed!")

if __name__ == "__main__":
    main()
