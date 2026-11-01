#!/usr/bin/env python3
"""
Master Orchestration Script: Run 50 Tasks across C3 and C4 on qwen2.5:14b and qwen2.5:32b.
Evaluates 200 task instances total (50 tasks x 2 categories x 2 models) across P0..P4.
Sequential execution guarantees 100% GPU VRAM residency (0% CPU offload) on TITAN RTX.
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime

# Root directory of ToolMaze
BASE_DIR = Path(__file__).resolve().parent.parent.parent

STAGES = [
    {
        "name": "Stage 1: qwen2.5:14b on Category C3 (50 tasks)",
        "model": "qwen2.5:14b",
        "category": "c3",
        "config": "evaluation/configs/gemini_eval_config_c3.yaml",
        "run_id": "qwen14b_care_c3_50",
    },
    {
        "name": "Stage 2: qwen2.5:14b on Category C4 (50 tasks)",
        "model": "qwen2.5:14b",
        "category": "c4",
        "config": "evaluation/configs/gemini_eval_config_c4.yaml",
        "run_id": "qwen14b_care_c4_50",
    },
    {
        "name": "Stage 3: qwen2.5:32b on Category C3 (50 tasks)",
        "model": "qwen2.5:32b",
        "category": "c3",
        "config": "evaluation/configs/gemini_eval_config_c3.yaml",
        "run_id": "qwen32b_care_c3_50",
    },
    {
        "name": "Stage 4: qwen2.5:32b on Category C4 (50 tasks)",
        "model": "qwen2.5:32b",
        "category": "c4",
        "config": "evaluation/configs/gemini_eval_config_c4.yaml",
        "run_id": "qwen32b_care_c4_50",
    },
]


def run_stage(stage: dict) -> dict:
    name = stage["name"]
    model = stage["model"]
    category = stage["category"]
    config = stage["config"]
    run_id = stage["run_id"]
    log_file = BASE_DIR / f"eval_{run_id}.log"

    print("\n" + "=" * 80)
    print(f"STARTING: {name}")
    print(f"Model: {model} | Category: {category} | Run ID: {run_id}")
    print(f"Log File: {log_file}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("=" * 80 + "\n", flush=True)

    cmd = [
        sys.executable,
        str(BASE_DIR / "evaluation/scripts/run_eval_care.py"),
        "--config", str(BASE_DIR / config),
        "--backend", "ollama",
        "--model", model,
        "--agent-type", "care",
        "--category", category,
        "--limit", "50",
        "--max-workers", "1",
        "--no-resume",
        "--run-id", run_id,
    ]

    t0 = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    env["PYTHONIOENCODING"] = "utf-8"

    with open(log_file, "w", encoding="utf-8") as f_log:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            env=env,
            stdout=f_log,
            stderr=subprocess.STDOUT,
        )

        print(f"[{run_id}] Process PID: {proc.pid}. Streaming progress...", flush=True)
        last_pos = 0

        while proc.poll() is None:
            time.sleep(3)
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8", errors="replace") as f_read:
                    f_read.seek(last_pos)
                    chunk = f_read.read()
                    if chunk:
                        last_pos += len(chunk.encode("utf-8", errors="replace"))
                        for line in chunk.splitlines():
                            if any(k in line for k in ["Starting", "Result:", "Telemetry", "Passed", "Failed", "PRR", "TSR", "ERROR", "WARNING", "Key Insights"]):
                                print(f"  [{run_id}] {line}", flush=True)

    dur = time.time() - t0
    retcode = proc.returncode
    print(f"\n[{run_id}] Finished with return code {retcode} in {dur:.1f}s ({dur/60:.1f}m).", flush=True)

    summary_file = BASE_DIR / f"evaluation/experiment_records/{run_id}/run_summary.json"
    if summary_file.exists():
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {summary_file}: {e}", flush=True)
    return {"run_id": run_id, "status": "no_summary_found", "return_code": retcode, "duration_s": dur}


def compile_comparison(all_results: dict):
    out_path = BASE_DIR / "evaluation/experiment_records/master_50_c3_c4_comparison.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "#" * 80)
    print("MASTER EVALUATION COMPLETE: ALL 4 EXPERIMENT RUNS FINISHED")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Consolidated results saved to: {out_path}")
    print("#" * 80 + "\n")


def main():
    print(f"=== ToolMaze 50-Task C3 & C4 Master Benchmark ===")
    print(f"Target Models: qwen2.5:14b, qwen2.5:32b")
    print(f"Categories: C3 (50 tasks), C4 (50 tasks)")
    print(f"Total Evaluations: 200 tasks (50x4)\n")

    overall_start = time.time()
    all_results = {}

    for stage in STAGES:
        res = run_stage(stage)
        all_results[stage["run_id"]] = res

    compile_comparison(all_results)
    tot_dur = time.time() - overall_start
    print(f"Total Wall-Clock Time: {tot_dur:.1f}s ({tot_dur/60:.1f} minutes).", flush=True)


if __name__ == "__main__":
    main()

