"""
Find inference files with API errors and optionally delete them.

Errors are classified into two categories:
  - retryable:  transient API/network issues → safe to delete and re-run
  - data_bug:   tool schema / request construction errors → need data fix first

Usage:
    # List all failed files (both categories)
    python evaluation/scripts/find_failed_inferences.py

    # List and delete only retryable failures
    python evaluation/scripts/find_failed_inferences.py --delete

    # List and delete data_bug failures too
    python evaluation/scripts/find_failed_inferences.py --delete --delete-bugs

    # Limit search to specific models or categories
    python evaluation/scripts/find_failed_inferences.py --model gemini-3-pro-preview --category c4

Output (always printed):
    A list of retryable task IDs for easy piping into re-eval script, e.g.:
        C4_task_002_P0
"""

import argparse
import json
import sys
from pathlib import Path

# Transient errors: safe to delete and re-run
RETRYABLE_PATTERNS = [
    "Request timed out",
    "APITimeoutError",
    "APIConnectionError",
    "RateLimitError",
    "InternalServerError",
    "bad_response_status_code",
    "502",
    "503",
]

# Data / schema bugs: retrying will not help, need to fix the task data
DATA_BUG_PATTERNS = [
    "TYPE_STRING",          # enum field has boolean instead of string
    "TYPE_INT",             # enum field has int instead of string
    "function_declarations",  # malformed tool schema rejected by API
    "upstream_error",       # API-side schema validation failure
    "invalid_request_error",
]

# Catch-all: any "Error during execution:" or "Error code:" not matched above
GENERIC_ERROR_PATTERNS = [
    "Error during execution:",
    "Error code:",
    "APIStatusError",
]


def classify_error(content: str) -> str:
    """Return 'retryable', 'data_bug', 'generic_error', or 'clean'."""
    for p in DATA_BUG_PATTERNS:
        if p in content:
            return "data_bug"
    for p in RETRYABLE_PATTERNS:
        if p in content:
            return "retryable"
    for p in GENERIC_ERROR_PATTERNS:
        if p in content:
            return "generic_error"
    return "clean"


def classify_inference(data: dict) -> str:
    """Return error class for an inference file, or 'clean'.

    Only the model's own final_answer is inspected for errors.  Tool outputs
    (role='tool') may contain error strings that are intentional perturbations
    injected into the dataset and must not be treated as inference failures.

    A missing final_answer is NOT automatically retryable: the model may have
    legitimately ended without one (e.g. stuck in a tool-call loop due to a
    perturbation).  We only flag it as retryable when the last assistant message
    indicates an agent-level error (e.g. a framework exception stored there).
    """
    messages = data.get("messages", [])

    # Primary check: look for errors in the model's final answer only.
    final_answers = [m for m in messages if m.get("type") == "final_answer"]
    if final_answers:
        last_content = str(final_answers[-1].get("content", ""))
        return classify_error(last_content)

    # No final_answer found.  Check whether the last assistant message carries
    # a framework-level error (not a tool response).  Tool messages are skipped
    # intentionally to avoid false positives from perturbation payloads.
    assistant_msgs = [
        m for m in messages
        if m.get("role") == "assistant" and m.get("type") != "tool_call"
    ]
    if assistant_msgs:
        last_content = str(assistant_msgs[-1].get("content", ""))
        error_class = classify_error(last_content)
        if error_class != "clean":
            return error_class

    # No final_answer and no detectable error in assistant messages.
    # Treat as clean — the model may have stopped mid-loop due to a perturbation,
    # which is valid evaluation data, not a broken inference run.
    return "clean"


def find_failed_files(results_root: Path, model_filter: str = None, category_filter: str = None):
    failed = []
    for inf_file in sorted(results_root.glob("*/fc/*/inferences/*_inference.json")):
        parts = inf_file.relative_to(results_root).parts
        model = parts[0]
        category = parts[2]

        if model_filter and model != model_filter:
            continue
        if category_filter and category != category_filter:
            continue

        try:
            with open(inf_file) as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] Cannot read {inf_file}: {e}", file=sys.stderr)
            continue

        error_class = classify_inference(data)
        if error_class != "clean":
            task_id = inf_file.stem.replace("_inference", "")
            failed.append({
                "model": model,
                "category": category,
                "task_id": task_id,
                "path": inf_file,
                "error_class": error_class,
            })

    return failed


def main():
    parser = argparse.ArgumentParser(description="Find (and optionally delete) failed inference files")
    parser.add_argument("--results-dir", default="evaluation/results",
                        help="Base results directory (default: evaluation/results)")
    parser.add_argument("--model", default=None, help="Filter by model name")
    parser.add_argument("--category", default=None, choices=["c1", "c2", "c3", "c4"],
                        help="Filter by task category")
    parser.add_argument("--delete", action="store_true",
                        help="Delete retryable + generic_error inference files")
    parser.add_argument("--delete-bugs", action="store_true",
                        help="Also delete data_bug inference files (use with --delete)")
    parser.add_argument("--delete-data-bug", action="store_true",
                        help="Delete data_bug inference files (standalone, no --delete needed)")
    args = parser.parse_args()

    results_root = Path(args.results_dir)
    if not results_root.exists():
        print(f"[ERROR] Results directory not found: {results_root}", file=sys.stderr)
        sys.exit(1)

    failed = find_failed_files(results_root, model_filter=args.model, category_filter=args.category)

    if not failed:
        print("No failed inference files found.")
        return

    retryable   = [x for x in failed if x["error_class"] in ("retryable", "generic_error")]
    data_bugs   = [x for x in failed if x["error_class"] == "data_bug"]

    def _print_group(items, label):
        if not items:
            return
        print(f"\n{'='*50}")
        print(f"  {label} ({len(items)})")
        print(f"{'='*50}")
        for item in items:
            print(f"  [{item['model']} / {item['category']}]  {item['task_id']}")
            print(f"    {item['path']}")

    _print_group(retryable, "RETRYABLE  (safe to delete & re-run)")
    _print_group(data_bugs, "DATA BUG   (need data fix, retrying won't help)")

    print(f"\nTotal: {len(failed)}  |  retryable: {len(retryable)}  |  data_bug: {len(data_bugs)}")

    # Always print bare retryable task IDs for piping into retry script
    if retryable:
        print("\n=== Retryable Task IDs (pipe into retry script) ===")
        for item in retryable:
            print(item["task_id"])

    if data_bugs:
        print("\n=== Data Bug Task IDs ===")
        for item in data_bugs:
            print(item["task_id"])

    if args.delete:
        to_delete = list(retryable)
        if args.delete_bugs:
            to_delete += data_bugs
        if to_delete:
            print(f"\nDeleting {len(to_delete)} file(s)...")
            for item in to_delete:
                item["path"].unlink()
                print(f"  Deleted: {item['path']}")
            print("Done.")
        else:
            print("\nNothing to delete.")
    else:
        print("\n(Run with --delete to remove retryable files; add --delete-bugs to also remove data_bug files)")

    if args.delete_data_bug:
        if data_bugs:
            print(f"\nDeleting {len(data_bugs)} data_bug file(s)...")
            for item in data_bugs:
                item["path"].unlink()
                print(f"  Deleted: {item['path']}")
            print("Done.")
        else:
            print("\nNo data_bug files to delete.")


if __name__ == "__main__":
    main()
