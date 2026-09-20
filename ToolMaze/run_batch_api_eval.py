#!/usr/bin/env python3
"""
Batch API evaluation runner.

Runs multiple models concurrently (both normal and p0-prompt variants).
After each run, deletes failed inference files and re-runs up to RETRY_ROUNDS times.

Usage:
    python3 run_batch_api_eval.py
    python3 run_batch_api_eval.py --categories c3 c4
    python3 run_batch_api_eval.py --modes P2 P4
    python3 run_batch_api_eval.py --inference-only
    python3 run_batch_api_eval.py --dry-run
"""

import argparse
import subprocess
import sys
import threading
from pathlib import Path

_print_lock = threading.Lock()

# ── Model registry ────────────────────────────────────────────────────────────
# key:   model name as used by the API
# value: max_workers (concurrent inference threads for this model)
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

# How many delete-and-retry rounds after the initial run
RETRY_ROUNDS = 3

# ── Shared settings ───────────────────────────────────────────────────────────
CATEGORIES  = ["c1", "c2", "c3", "c4"]
MODES       = ["P0", "P1", "P2", "P3", "P4"]
PROJECT_ROOT = Path(__file__).resolve().parent


# ── Helpers ───────────────────────────────────────────────────────────────────

def log(tag: str, msg: str) -> None:
    with _print_lock:
        print(f"[{tag}] {msg}", flush=True)


def run_api_eval(model: str, max_workers: int, categories: list[str], modes: list[str],
                 p0_prompt: bool, inference_only: bool, dry_run: bool) -> int:
    """Invoke run_api_eval.py for one (model, p0_prompt) combination."""
    cmd = [
        "python3", "run_api_eval.py",
        "--models", model,
        "--categories", *categories,
        "--modes", *modes,
        "--max-workers", str(max_workers),
    ]
    if p0_prompt:
        cmd.append("--p0-prompt")
    if inference_only:
        cmd.append("--inference-only")
    if dry_run:
        cmd.append("--dry-run")

    tag = f"{model}{'_p0prompt' if p0_prompt else ''}"
    log(tag, "Starting: " + " ".join(cmd))
    if dry_run:
        return 0
    log_path = PROJECT_ROOT / f"batch_eval_{tag}.log"
    log(tag, f"stdout/stderr → {log_path}")
    with open(log_path, "a") as lf:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, stdout=lf, stderr=lf)
    return result.returncode


def delete_failed(model: str, p0_prompt: bool, dry_run: bool) -> int:
    """Run find_failed_inferences.py --delete for this model (with result_tag if p0)."""
    result_model = f"{model}_p0prompt" if p0_prompt else model
    cmd = [
        "python3", "evaluation/scripts/find_failed_inferences.py",
        "--model", result_model,
        "--delete",
    ]
    tag = f"{result_model}"
    log(tag, "Deleting failed inferences: " + " ".join(cmd))
    if dry_run:
        return 0
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def run_one_variant(model: str, max_workers: int, categories: list[str], modes: list[str],
                    p0_prompt: bool, inference_only: bool, dry_run: bool) -> None:
    """Full lifecycle for one (model, p0_prompt) variant: initial run + retry rounds."""
    tag = f"{model}{'_p0prompt' if p0_prompt else ''}"

    # Initial run
    rc = run_api_eval(model, max_workers, categories, modes,
                      p0_prompt, inference_only, dry_run)
    if rc != 0:
        log(tag, f"[warn] run_api_eval returned {rc}")

    # Delete-and-retry loop
    for round_idx in range(1, RETRY_ROUNDS + 1):
        log(tag, f"Retry round {round_idx}/{RETRY_ROUNDS}: deleting failed inferences...")
        delete_failed(model, p0_prompt, dry_run)

        log(tag, f"Retry round {round_idx}/{RETRY_ROUNDS}: re-running eval...")
        rc = run_api_eval(model, max_workers, categories, modes,
                          p0_prompt, inference_only, dry_run)
        if rc != 0:
            log(tag, f"[warn] retry round {round_idx} returned {rc}")

    log(tag, "All rounds completed.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Batch concurrent API eval runner")
    parser.add_argument("--categories",     nargs="+", default=CATEGORIES,
                        choices=["c1", "c2", "c3", "c4"])
    parser.add_argument("--modes",          nargs="+", default=MODES,
                        choices=["P0", "P1", "P2", "P3", "P4"])
    parser.add_argument("--inference-only", action="store_true",
                        help="Run inference only, skip judge")
    parser.add_argument("--dry-run",        action="store_true",
                        help="Print commands without executing")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Batch API Eval  —  {len(MODELS)} model(s) x 2 variants")
    print(f"  Categories : {args.categories}")
    print(f"  Modes      : {args.modes}")
    print(f"  Retry rounds: {RETRY_ROUNDS}")
    print(f"{'='*60}\n")

    # Launch every (model, p0_prompt) variant in a separate thread
    threads: list[threading.Thread] = []
    for model, max_workers in MODELS.items():
        for p0_prompt in (False, True):

            t = threading.Thread(
                target=run_one_variant,
                args=(model, max_workers, args.categories, args.modes,
                      p0_prompt, args.inference_only, args.dry_run),
                name=f"{model}{'_p0prompt' if p0_prompt else ''}",
                daemon=False,
            )
            threads.append(t)

    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
            log(t.name, "Thread finished.")
    except KeyboardInterrupt:
        print("\n[batch] Ctrl+C received — waiting for subprocesses to exit...", flush=True)
        for t in threads:
            t.join()
        print("[batch] All threads stopped.", flush=True)
        sys.exit(1)

    print(f"\n{'='*60}")
    print("  All batch eval threads completed.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
