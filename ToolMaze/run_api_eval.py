#!/usr/bin/env python3
"""
API-based LLM evaluation runner.

Runs full eval (C1-C4 x P0-P4) against a remote OpenAI-compatible API endpoint.
No local vLLM deployment needed.

Usage:
    python3 run_api_eval.py --models gpt-4o                    # single model
    python3 run_api_eval.py --models gpt-4o gemini-2.0-flash   # multiple models
    python3 run_api_eval.py --models gpt-4o --categories c3 c4 # limit categories
    python3 run_api_eval.py --models gpt-4o --modes P2 P4      # limit modes
    python3 run_api_eval.py --models gpt-4o --inference-only   # skip judge
    python3 run_api_eval.py --models gpt-4o --p0-prompt        # force P0 system prompt
    python3 run_api_eval.py --models gpt-4o --dry-run          # print commands only
"""

import argparse
import subprocess
import sys
from pathlib import Path

# ── API credentials (hardcoded) ───────────────────────────────────────────────
# If empty, falls back to the base_url / api_key defined in BASE_CONFIG.
API_BASE_URL = ""
API_KEY      = ""

# ── Eval settings ─────────────────────────────────────────────────────────────
CATEGORIES = ["c1", "c2", "c3", "c4"]
MODES      = ["P0", "P1", "P2", "P3", "P4"]

# Base config template (judge settings, data paths, etc.)
BASE_CONFIG = "evaluation/configs/openai_eval_config_c1.yaml"

PROJECT_ROOT = Path(__file__).resolve().parent


# ── Config generation ─────────────────────────────────────────────────────────

def make_config(model_name: str, category: str, dry_run: bool,
                p0_prompt: bool = False, max_workers: int = None) -> Path:
    """
    Write a per-(model, category) YAML config derived from BASE_CONFIG.
    Returns the path to the written config file.
    """
    import yaml

    base = Path(BASE_CONFIG)
    with open(base) as f:
        cfg = yaml.safe_load(f)

    # Agent override
    result_model_name = f"{model_name}_p0prompt" if p0_prompt else model_name
    cfg["agent"]["type"]            = "openai"
    cfg["agent"]["model"]           = model_name          # used for API calls
    if API_BASE_URL:
        cfg["agent"]["base_url"]    = API_BASE_URL
    if API_KEY:
        cfg["agent"]["api_key"]     = API_KEY
    cfg["agent"]["force_p0_prompt"] = p0_prompt
    if p0_prompt:
        cfg["agent"]["result_tag"]  = "p0prompt"
    else:
        cfg["agent"].pop("result_tag", None)

    # Data paths override for this category
    cfg["data"]["task_dir"]      = f"data/perturbed_tasks/{category}"
    cfg["data"]["task_category"] = category

    if max_workers is not None:
        cfg["evaluation"]["max_workers"] = max_workers

    out_path = PROJECT_ROOT / f".tmp_api_eval_config_{result_model_name}_{category}.yaml"
    if not dry_run:
        with open(out_path, "w") as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    return out_path


# ── Eval runner ───────────────────────────────────────────────────────────────

def run_eval(config_path: Path, modes: list[str],
             inference_only: bool, dry_run: bool) -> int:
    cmd = [
        "python3", "evaluation/scripts/run_eval.py",
        "--config", str(config_path),
        "--modes", *modes,
    ]
    if inference_only:
        cmd.append("--inference-only")
    print(f"[eval] {' '.join(cmd)}")
    if dry_run:
        return 0
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="API-based eval runner")
    parser.add_argument("--models",     nargs="+", required=True,
                        help="Model name(s) as recognized by the API (e.g. gpt-4o)")
    parser.add_argument("--categories", nargs="+", default=CATEGORIES,
                        choices=["c1", "c2", "c3", "c4"],
                        help="Categories to eval (default: c1 c2 c3 c4)")
    parser.add_argument("--modes",      nargs="+", default=MODES,
                        choices=["P0", "P1", "P2", "P3", "P4"],
                        help="Modes to eval (default: P0-P4)")
    parser.add_argument("--inference-only", action="store_true",
                        help="Run inference only, skip judge")
    parser.add_argument("--max-workers",    type=int, default=None,
                        help="Parallel worker count (default: value in config, currently 4)")
    parser.add_argument("--p0-prompt",      action="store_true",
                        help="Force P0 system prompt for all modes")
    parser.add_argument("--dry-run",        action="store_true",
                        help="Print commands without executing")
    args = parser.parse_args()

    tag = " [p0-prompt]" if args.p0_prompt else ""
    for model_name in args.models:
        print(f"\n{'='*60}")
        print(f"  Model : {model_name}{tag}")
        print(f"  URL   : {API_BASE_URL}")
        print(f"  Cats  : {args.categories}")
        print(f"  Modes : {args.modes}")
        print(f"{'='*60}")

        failed_cats = []
        for cat in args.categories:
            config_path = make_config(model_name, cat, args.dry_run,
                                      args.p0_prompt, args.max_workers)
            rc = run_eval(config_path, args.modes, args.inference_only, args.dry_run)
            if not args.dry_run and config_path.exists():
                config_path.unlink()
            if rc != 0:
                print(f"[warn] eval returned non-zero for {model_name}/{cat}: {rc}")
                failed_cats.append(cat)

        if failed_cats:
            print(f"[warn] {model_name}: failed categories: {failed_cats}")
        else:
            print(f"[done] {model_name}: all categories completed.")

    print("\n[done] All models evaluated.")


if __name__ == "__main__":
    main()
