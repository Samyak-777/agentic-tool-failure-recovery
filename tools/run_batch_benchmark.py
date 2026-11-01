"""
tools/run_batch_benchmark.py
Orchestrates large-scale comparative benchmark runs between Baseline Agent and CARE Agent
across multiple model backends (Qwen, Llama, Gemini) and ToolMaze topologies (C1, C2).
Produces consolidated markdown and LaTeX metric tables for research publication.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BenchmarkOrchestrator")

def run_command_stream(cmd: List[str], cwd: Path) -> int:
    logger.info(f"Executing: {' '.join(cmd)} in {cwd}")
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    for line in iter(proc.stdout.readline, ""):
        print(line, end="", flush=True)
    proc.stdout.close()
    return proc.wait()

def parse_args():
    parser = argparse.ArgumentParser(description="Run batched ToolMaze evaluations")
    parser.add_argument("--server", action="store_true", help="Running on server environment")
    parser.add_argument("--categories", nargs="+", default=["c1", "c2"], help="Categories (c1, c2)")
    parser.add_argument("--modes", default="P0,P1,P2,P3,P4", help="Comma-separated perturbation modes")
    parser.add_argument("--limit-c1", type=int, default=20, help="Task limit for C1")
    parser.add_argument("--limit-c2", type=int, default=10, help="Task limit for C2")
    parser.add_argument("--models", nargs="+", default=["qwen3:8b", "gemini-2.5-flash"], help="Models to benchmark")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    logger.info(f"Starting Benchmark Suite for Models: {args.models}, Categories: {args.categories}")
