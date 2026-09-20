"""Main evaluation script for C1/C2/C3/C4 tasks.

Supports parallel execution and multiple agent types.

Usage:
    # Run evaluation with default config
    python evaluation/scripts/run_eval.py

    # Run with custom config
    python evaluation/scripts/run_eval.py --config path/to/config.yaml

    # Run specific modes only
    python evaluation/scripts/run_eval.py --modes P0 P1 P3

    # Run single task (task category auto-inferred from task_id)
    python evaluation/scripts/run_eval.py --task-id C2_task_002_P1

    # Override task category without editing YAML
    python evaluation/scripts/run_eval.py --task-category c2 --modes P0 P1 P2 P3 P4

    # Run with specific agent
    python evaluation/scripts/run_eval.py --agent-type openai --model gpt-4o
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml

# Add project root to path. Inserting the project root makes both `evaluation`
# and `tools` importable as top-level packages — the latter is required because
# some plugins do `from tools.plugins import ...`.
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from evaluation.core import ExecutionEngine, JudgeSystem, MetricsCalculator
from evaluation.utils import ResultSaver


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_TASK_DIRS = {
    "c1": "data/perturbed_tasks/c1",
    "c2": "data/perturbed_tasks/c2",
    "c3": "data/perturbed_tasks/c3",
    "c4": "data/perturbed_tasks/c4",
}


def infer_task_category_from_task_id(task_id: Optional[str]) -> Optional[str]:
    """Infer task category from task ID prefix (C1_/C2_/C3_/C4_)."""
    if not task_id:
        return None

    # 统一转大写后匹配前缀
    task_id_upper = task_id.upper()
    if task_id_upper.startswith("C1_"):
        return "c1"
    if task_id_upper.startswith("C2_"):
        return "c2"
    if task_id_upper.startswith("C3_"):
        return "c3"
    if task_id_upper.startswith("C4_"):
        return "c4"
    return None


def infer_task_category_from_task_dir(task_dir: Optional[str]) -> Optional[str]:
    """Infer task category from task directory suffix (.../c1 or .../c2 or .../c3 or .../c4)."""
    if not task_dir:
        return None

    normalized = task_dir.replace("\\", "/").rstrip("/").lower()
    if normalized.endswith("/c1"):
        return "c1"
    if normalized.endswith("/c2"):
        return "c2"
    if normalized.endswith("/c3"):
        return "c3"
    if normalized.endswith("/c4"):
        return "c4"
    return None


def apply_task_data_overrides(config: Dict[str, Any], args: argparse.Namespace) -> None:
    """Apply CLI overrides for task category and task directory."""
    task_id_category = infer_task_category_from_task_id(args.task_id)

    # 检查 task_id 与显式指定的 category 是否冲突
    if args.task_category and task_id_category and args.task_category != task_id_category:
        raise ValueError(
            f"Task category conflict: --task-id implies '{task_id_category}' but "
            f"--task-category is '{args.task_category}'"
        )

    if args.task_dir:
        config["data"]["task_dir"] = args.task_dir

    # 优先使用显式指定的 category，并设置对应默认 task_dir
    if args.task_category:
        config["data"]["task_category"] = args.task_category
        if not args.task_dir:
            config["data"]["task_dir"] = DEFAULT_TASK_DIRS[args.task_category]
        return

    # 其次从 task_dir 推断 category
    if args.task_dir:
        inferred_from_dir = infer_task_category_from_task_dir(args.task_dir)
        if inferred_from_dir:
            config["data"]["task_category"] = inferred_from_dir
        return

    # 最后从 task_id 推断 category 与默认目录
    if task_id_category:
        config["data"]["task_category"] = task_id_category
        config["data"]["task_dir"] = DEFAULT_TASK_DIRS[task_id_category]


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # 递归展开 ${VAR} 形式的环境变量
    def expand_env(obj):
        if isinstance(obj, dict):
            return {k: expand_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [expand_env(v) for v in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.environ.get(env_var, obj)
        return obj

    return expand_env(config)


def load_tasks(
    task_dir: str,
    modes: Optional[List[str]] = None,
    task_id: Optional[str] = None,
    offset: int = 0,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Load task JSON files.

    New data format: All task files are directly in task_dir (e.g., C1_task_001_P0.json)

    Args:
        task_dir: Directory containing task files
        modes: Optional list of modes to filter
        task_id: Optional specific task ID to load (e.g., "C1_task_001_P0")
        offset: Skip the first N tasks (after sorting)
        limit: Maximum number of tasks to return (after offset)

    Returns:
        List of task dictionaries
    """
    task_dir = Path(task_dir)
    tasks = []

    if task_id:
        # 按指定 task_id 加载单个任务
        task_file = task_dir / f"{task_id}.json"
        if task_file.exists():
            with open(task_file, 'r') as f:
                tasks.append(json.load(f))
        return tasks

    # 按字典序加载目录下所有 JSON 任务文件
    for task_file in sorted(task_dir.glob("*.json")):
        try:
            with open(task_file, 'r') as f:
                task = json.load(f)

                # 若指定了 modes 则过滤不匹配的任务
                task_mode = task.get("perturbation_mode", "P0")
                if modes and task_mode not in modes:
                    continue

                tasks.append(task)
        except Exception as e:
            logger.error(f"Failed to load {task_file}: {e}")

    # 应用 offset 与 limit 切片
    if offset or limit is not None:
        tasks = tasks[offset: (offset + limit) if limit is not None else None]

    return tasks


def create_agent(config: Dict[str, Any]):
    """Create agent instance from config.

    Args:
        config: Configuration dictionary

    Returns:
        Agent instance
    """
    agent_config = config["agent"]
    agent_type = agent_config["type"].lower()

    # 根据类型导入并实例化对应 Agent
    if agent_type == "openai":
        from evaluation.agents import OpenAIAgent
        agent = OpenAIAgent(
            model=agent_config["model"],
            api_key=agent_config.get("api_key"),
            base_url=agent_config.get("base_url"),
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"]
        )
    elif agent_type == "anthropic":
        from evaluation.agents import AnthropicAgent
        agent = AnthropicAgent(
            model=agent_config["model"],
            api_key=agent_config.get("api_key"),
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"]
        )
    elif agent_type == "vllm":
        from evaluation.agents import VLLMAgent
        agent = VLLMAgent(
            model=agent_config["model"],
            base_url=agent_config["base_url"],
            api_key=agent_config.get("api_key", "EMPTY"),
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"]
        )
    elif agent_type == "mcp":
        from evaluation.agents import MCPAgent
        agent = MCPAgent(
            model=agent_config["model"],
            api_key=agent_config.get("api_key"),
            base_url=agent_config.get("base_url"),
            temperature=agent_config["temperature"],
            max_tokens=agent_config["max_tokens"]
        )
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # 若配置强制 P0 提示则写入 Agent 属性
    if agent_config.get("force_p0_prompt") and hasattr(agent, "force_p0_prompt"):
        agent.force_p0_prompt = True
    return agent


def evaluate_single_task(
    task_json: Dict[str, Any],
    config: Dict[str, Any],
    tools_dir: str,
    judge: JudgeSystem,
    saver: ResultSaver
) -> Dict[str, Any]:
    """Evaluate a single task.

    Logic:
    1. Check if inference exists locally
    2. If exists, skip inference and load it
    3. If not exists, run inference and save it
    4. Run evaluation (judge) on the inference result

    Args:
        task_json: Task specification
        config: Configuration
        tools_dir: Tools directory path
        judge: Judge system
        saver: Result saver

    Returns:
        Evaluation result
    """
    task_id = task_json["task_id"]
    mode = task_json.get("perturbation_mode", "P0")

    logger.info(f"Processing {task_id} (Mode: {mode})")

    try:
        # 步骤1：若本地已存在推理结果则直接加载
        if saver.inference_exists(task_id, mode):
            logger.info(f"  ✓ Inference exists, loading from disk")
            inference_data = saver.load_inference(task_id, mode)
            tokens = inference_data.get("tokens", {})
            legacy_tokens = inference_data.get("token_usage", {})
            token_usage = {
                "input_tokens": tokens.get("input_tokens", legacy_tokens.get("prompt_tokens", 0)),
                "output_tokens": tokens.get("output_tokens", legacy_tokens.get("completion_tokens", 0)),
                "total_tokens": tokens.get("total_tokens", legacy_tokens.get("total_tokens", 0))
            }
        else:
            # 步骤2：运行推理并保存结果
            logger.info(f"  → Running inference...")
            agent = create_agent(config)
            engine = ExecutionEngine(task_json, agent, tools_dir=tools_dir)
            trace_logger, token_usage = engine.run(max_rounds=config["execution"]["max_rounds"])

            inference_data = trace_logger.to_dict(token_usage=token_usage)
            saver.save_inference(task_id, mode, trace_logger, token_usage)
            logger.info(f"  ✓ Inference saved | Tokens: {token_usage['total_tokens']}")

        # 步骤3：执行评测（仅推理模式则跳过）
        if judge is None:
            return {
                "task_id": task_id,
                "mode": mode,
                "passed": None,
                "tokens": token_usage["total_tokens"],
                "task_json": task_json,
                "inference_data": inference_data,
            }

        logger.info(f"  → Running evaluation...")
        judgement = judge.judge(task_json, inference_data)
        saver.save_evaluation(task_id, mode, judgement)

        logger.info(f"  ✓ Result: {'PASS' if judgement['pass'] else 'FAIL'}")

        return {
            "task_id": task_id,
            "mode": mode,
            "passed": judgement["pass"],
            "tokens": token_usage["total_tokens"],
            "judgement": judgement,
            "task_json": task_json,
            "inference_data": inference_data,
        }

    except Exception as e:
        logger.error(f"  ✗ Error: {e}", exc_info=True)
        return {
            "task_id": task_id,
            "mode": mode,
            "passed": False,
            "tokens": 0,
            "error": str(e)
        }


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Run evaluation for C1/C2/C3/C4 tasks")
    parser.add_argument("--config", type=str, default="evaluation/configs/openai_eval_config_c1.yaml",
                        help="Path to config file")
    parser.add_argument("--modes", nargs="+", default=None,
                        help="Modes to evaluate (e.g., P0 P1 P3)")
    parser.add_argument("--task-id", type=str, default=None,
                        help="Specific task ID to evaluate")
    parser.add_argument("--task-category", type=str, choices=["c1", "c2", "c3", "c4"], default=None,
                        help="Task category override (c1/c2/c3/c4); also sets default task_dir")
    parser.add_argument("--task-dir", type=str, default=None,
                        help="Task directory override")
    parser.add_argument("--agent-type", type=str, default=None,
                        help="Agent type (openai, anthropic, vllm, mcp)")
    parser.add_argument("--model", type=str, default=None,
                        help="Model name")
    parser.add_argument("--no-parallel", action="store_true",
                        help="Disable parallel execution")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip the first N tasks (0-based, applied after mode filtering)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum number of tasks to run (applied after --offset)")
    parser.add_argument("--inference-only", action="store_true",
                        help="Run inference only, skip judge and metrics")

    args = parser.parse_args()

    # 加载配置
    logger.info(f"Loading config from {args.config}")
    config = load_config(args.config)

    # 用 CLI 参数覆盖配置
    if args.modes:
        config["evaluation"]["modes"] = args.modes
    if args.agent_type:
        config["agent"]["type"] = args.agent_type
    if args.model:
        config["agent"]["model"] = args.model
    if args.no_parallel:
        config["evaluation"]["parallel"] = False
    apply_task_data_overrides(config, args)

    # 初始化评测组件
    logger.info("Initializing components...")
    logger.info(
        f"Task selection | category={config['data'].get('task_category')} "
        f"| task_dir={config['data'].get('task_dir')}"
    )

    tools_dir = config["data"]["tools_dir"]

    # 仅在非仅推理模式下初始化 Judge（按需导入 OpenAI）
    if not args.inference_only:
        try:
            from openai import OpenAI
            judge_client = OpenAI(
                api_key=config["judge"]["api_key"],
                base_url=config["judge"].get("base_url")
            )
            judge = JudgeSystem(llm_client=judge_client, model=config["judge"]["model"],
                                template_dir=config["data"].get("template_dir"))
            logger.info("Judge initialized with LLM client")
        except ImportError:
            logger.warning("OpenAI package not found, judge will run without LLM semantic matching")
            judge = JudgeSystem(llm_client=None, model=config["judge"]["model"],
                                template_dir=config["data"].get("template_dir"))
    else:
        judge = None
        logger.info("Inference-only mode: judge skipped")

    metrics = MetricsCalculator()

    # 根据 agent 类型确定输出目录分类（fc 或 mcp）
    agent_type = config["agent"]["type"].lower()
    agent_type_dir = "mcp" if agent_type == "mcp" else "fc"

    saver = ResultSaver(
        base_dir=config["data"]["output_dir"],
        model=config["agent"]["model"] + (
            f"_{config['agent']['result_tag']}"
            if config["agent"].get("result_tag") else ""
        ),
        agent_type=agent_type_dir,
        task_category=config["data"].get("task_category", "c1")
    )

    # 加载任务列表
    logger.info("Loading tasks...")
    tasks = load_tasks(
        config["data"]["task_dir"],
        modes=config["evaluation"]["modes"],
        task_id=args.task_id,
        offset=args.offset,
        limit=args.limit,
    )
    logger.info(f"Loaded {len(tasks)} tasks")

    if not tasks:
        logger.error("No tasks found!")
        return

    # 执行评测
    logger.info("Starting evaluation...")

    if config["evaluation"]["parallel"] and not args.task_id:
        # 并行执行（使用线程池避免 pickle 问题）
        max_workers = config["evaluation"].get("max_workers", 16)
        logger.info(f"Running in parallel with {max_workers} workers (threaded)")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for task in tasks:
                future = executor.submit(
                    evaluate_single_task,
                    task, config, tools_dir, judge, saver
                )
                futures.append(future)

            for future in as_completed(futures):
                result = future.result()
                if "error" not in result and result.get("judgement"):
                    metrics.add_result(
                        result["task_json"],
                        result["inference_data"],
                        result["judgement"],
                    )
    else:
        # 串行执行
        logger.info("Running sequentially")
        for task in tasks:
            result = evaluate_single_task(
                task, config, tools_dir, judge, saver
            )
            if "error" not in result and result.get("judgement"):
                metrics.add_result(
                    result["task_json"],
                    result["inference_data"],
                    result["judgement"],
                )

    # 生成并保存指标报告
    logger.info("Generating metrics report...")

    # 合并本次运行之外已存在磁盘上的结果，确保最终报告覆盖所有已完成任务
    evaluated_keys = {
        (r["task_id"], r["mode"])
        for r in metrics.results
    }
    merged_count = 0
    for task_id, mode in saver.list_completed_tasks():
        if (task_id, mode) in evaluated_keys:
            continue  # 本次已评测，跳过
        # 从数据目录重建 task_json 以正确计算 oracle recovery calls
        task_file = Path(config["data"]["task_dir"]) / f"{task_id}_{mode}.json"
        if not task_file.exists():
            # 兼容旧布局：尝试不带 mode 后缀的文件名
            task_file = Path(config["data"]["task_dir"]) / f"{task_id}.json"
        if not task_file.exists():
            logger.warning(f"  [merge] task file not found for {task_id}_{mode}, skipping")
            continue
        try:
            with open(task_file) as f:
                task_json = json.load(f)
            inference_data = saver.load_inference(task_id, mode)
            judgement = saver.load_evaluation(task_id, mode)
            metrics.add_result(task_json, inference_data, judgement)
            merged_count += 1
        except Exception as e:
            logger.warning(f"  [merge] failed to load {task_id}_{mode}: {e}")

    if merged_count:
        logger.info(f"Merged {merged_count} pre-existing result(s) into metrics")

    report = metrics.generate_report()
    report_path = saver.save_metrics(report)
    logger.info(f"Metrics saved to {report_path}")

    # 打印汇总
    print("\n" + metrics.print_summary(report))

    logger.info("Evaluation completed!")


if __name__ == "__main__":
    main()
