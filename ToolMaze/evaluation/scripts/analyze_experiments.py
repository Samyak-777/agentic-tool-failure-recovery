"""
ToolMaze Offline Failure Analysis and Experiment Comparison Pipeline.

Reads saved experiment records from ToolMaze/evaluation/experiment_records/
and produces comprehensive causal attribution, diagnostic metric aggregations,
comparative CSV tables, and Markdown reports WITHOUT invoking any LLM APIs or re-executing tasks.
"""

import os
import sys
import json
import csv
import argparse
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
import statistics

# Ensure ToolMaze project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.telemetry.schema import (
    CausalAttribution,
    SCHEMA_VERSION
)


def extract_tokens(tr: Dict[str, Any]) -> int:
    toks = tr.get("tokens")
    if isinstance(toks, dict):
        return int(toks.get("total_tokens", 0) or 0)
    elif isinstance(toks, (int, float)):
        return int(toks)
    elif isinstance(toks, str) and toks.isdigit():
        return int(toks)
    return 0


def safe_div(num: float, den: float, default: float = 0.0) -> float:
    return (num / den) if den > 0 else default


class ExperimentAnalyzer:
    """Offline analyzer that operates on saved experiment records."""

    def __init__(
        self,
        records_dir: Path,
        run_ids: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        modes: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        output_dir: Optional[Path] = None
    ):
        self.records_dir = records_dir
        self.run_ids = run_ids
        self.categories = [c.upper() for c in categories] if categories else None
        self.modes = [m.upper() for m in modes] if modes else None
        self.task_ids = set(task_ids) if task_ids else None
        self.models = set(models) if models else None

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir or (self.records_dir / f"analysis_{ts}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.runs: Dict[str, Dict[str, Any]] = {}
        self.task_records: List[Dict[str, Any]] = []
        self.skipped_records: List[Dict[str, Any]] = []

    def load_records(self) -> None:
        """Scan experiment records directory and load matching run manifests and task records."""
        if not self.records_dir.exists():
            print(f"Warning: Records directory {self.records_dir} does not exist.")
            return

        run_dirs = []
        if self.run_ids:
            for rid in self.run_ids:
                p = self.records_dir / rid
                if p.is_dir():
                    run_dirs.append(p)
                else:
                    print(f"Warning: Requested run directory {p} not found.")
        else:
            for p in sorted(self.records_dir.iterdir()):
                if p.is_dir() and not p.name.startswith("analysis_"):
                    run_dirs.append(p)

        print(f"Found {len(run_dirs)} run directory/directories to analyze.")

        for rdir in run_dirs:
            run_id = rdir.name
            manifest_file = rdir / "run_manifest.json"
            manifest = {}
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load manifest for {run_id}: {e}")

            self.runs[run_id] = manifest
            tasks_dir = rdir / "task_records"
            if not tasks_dir.exists():
                continue

            for tfile in sorted(tasks_dir.glob("*.json")):
                try:
                    with open(tfile, "r", encoding="utf-8") as f:
                        record = json.load(f)

                    # Filters
                    if self.categories and record.get("complexity", "").upper() not in self.categories:
                        continue
                    if self.modes and record.get("mode", "").upper() not in self.modes:
                        continue
                    if self.task_ids and record.get("task_id") not in self.task_ids:
                        continue
                    if self.models and record.get("model") not in self.models:
                        continue

                    # Attach run_id if missing
                    record.setdefault("run_id", run_id)
                    record["_source_file"] = str(tfile)
                    self.task_records.append(record)
                except Exception as e:
                    self.skipped_records.append({"file": str(tfile), "error": str(e)})

        print(f"Loaded {len(self.task_records)} task records across {len(self.runs)} runs (skipped {len(self.skipped_records)}).")

    def run_analysis(self) -> Dict[str, Any]:
        """Compute all offline failure analyses, causal attributions, and diagnostic metrics."""
        report: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "runs_analyzed": list(self.runs.keys()),
            "total_tasks_analyzed": len(self.task_records),
            "skipped_records_count": len(self.skipped_records),
            "skipped_records": self.skipped_records
        }

        # 1. Overall and By-Mode Success (TSR, PRR, RC)
        report["metrics"] = self._compute_metrics_summary()

        # 2. Causal Attribution Breakdown
        report["causal_attribution"] = self._compute_causal_attribution()

        # 3. Tool Failure Analysis
        report["tool_failures"] = self._compute_tool_failures()

        # 4. Failure Stages and Categories
        report["failure_categories"] = self._compute_failure_categories()

        # 5. Recovery and DAG Rerouting Analysis
        report["recovery_analysis"] = self._compute_recovery_analysis()

        # 6. Baseline vs CARE Comparison
        report["baseline_vs_care"] = self._compute_agent_comparison()

        # 7. Diagnostic Deep Metrics
        report["diagnostic_metrics"] = self._compute_diagnostic_metrics()

        # Export outputs
        self._export_csvs(report)
        self._export_json(report)
        self._export_markdown_report(report)

        return report

    def _compute_metrics_summary(self) -> Dict[str, Any]:
        """Compute TSR, pass counts, token usage, latency by mode and complexity."""
        modes_stat = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0, "tokens": [], "durations": []})
        complexities_stat = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0})

        for tr in self.task_records:
            m = tr.get("mode", "P0")
            c = tr.get("complexity", "C1")
            passed = tr.get("passed") is True

            modes_stat[m]["total"] += 1
            complexities_stat[c]["total"] += 1

            if passed:
                modes_stat[m]["passed"] += 1
                complexities_stat[c]["passed"] += 1
            else:
                modes_stat[m]["failed"] += 1
                complexities_stat[c]["failed"] += 1

            total_tok = extract_tokens(tr)
            if total_tok:
                modes_stat[m]["tokens"].append(total_tok)

            # Measure duration if available
            st = tr.get("start_time")
            et = tr.get("end_time")
            if st and et:
                try:
                    dt1 = datetime.datetime.fromisoformat(st)
                    dt2 = datetime.datetime.fromisoformat(et)
                    dur = (dt2 - dt1).total_seconds()
                    if dur >= 0:
                        modes_stat[m]["durations"].append(dur)
                except Exception:
                    pass

        summary: Dict[str, Any] = {"by_mode": {}, "by_complexity": {}}
        for m, s in modes_stat.items():
            tot = s["total"]
            p = s["passed"]
            summary["by_mode"][m] = {
                "total": tot,
                "passed": p,
                "failed": s["failed"],
                "tsr": safe_div(p, tot),
                "mean_tokens": statistics.mean(s["tokens"]) if s["tokens"] else 0.0,
                "mean_duration_sec": statistics.mean(s["durations"]) if s["durations"] else 0.0
            }

        for c, s in complexities_stat.items():
            tot = s["total"]
            p = s["passed"]
            summary["by_complexity"][c] = {
                "total": tot,
                "passed": p,
                "failed": s["failed"],
                "tsr": safe_div(p, tot)
            }

        return summary

    def _compute_causal_attribution(self) -> Dict[str, Any]:
        """Aggregate causal attribution categories with exact sample sizes and evidence."""
        attr_counts = defaultdict(lambda: {"count": 0, "sample_tasks": []})
        configured_vs_activated = {
            "total_configured_perturbations": 0,
            "total_activated_perturbations": 0,
            "tasks_with_configured": 0,
            "tasks_with_activated": 0,
            "tasks_recovered": 0
        }

        for tr in self.task_records:
            ca = tr.get("causal_attribution", {})
            attr_type = ca.get("attribution", CausalAttribution.INSUFFICIENT_TELEMETRY.value)
            attr_counts[attr_type]["count"] += 1
            if len(attr_counts[attr_type]["sample_tasks"]) < 5:
                attr_counts[attr_type]["sample_tasks"].append(tr.get("task_id"))

            pt = tr.get("perturbation_tracking", {})
            cfg = pt.get("configured", [])
            acts = pt.get("activations", [])

            if cfg:
                configured_vs_activated["tasks_with_configured"] += 1
                configured_vs_activated["total_configured_perturbations"] += len(cfg)
            if acts:
                configured_vs_activated["tasks_with_activated"] += 1
                configured_vs_activated["total_activated_perturbations"] += len(acts)
                if tr.get("passed") is True:
                    configured_vs_activated["tasks_recovered"] += 1

        total_tasks = len(self.task_records)
        attribution_breakdown = {}
        for k, v in attr_counts.items():
            attribution_breakdown[k] = {
                "count": v["count"],
                "total": total_tasks,
                "rate": safe_div(v["count"], total_tasks),
                "sample_tasks": v["sample_tasks"]
            }

        return {
            "attribution_breakdown": attribution_breakdown,
            "configured_vs_activated": configured_vs_activated
        }

    def _compute_tool_failures(self) -> Dict[str, Any]:
        """Compute failure rates by individual tool, repeated failures, and semantic invalid output rates."""
        tool_invocations = defaultdict(lambda: {"invocations": 0, "failures": 0, "perturbed_calls": 0, "invalid_validation": 0})
        repeated_failure_calls = defaultdict(int)

        for tr in self.task_records:
            task_failed_tools = set()
            for tc in tr.get("tool_calls", []):
                tname = tc.get("tool_name", "unknown_tool")
                tool_invocations[tname]["invocations"] += 1
                if tc.get("is_perturbed"):
                    tool_invocations[tname]["perturbed_calls"] += 1
                if tc.get("validation_status") == "INVALID":
                    tool_invocations[tname]["invalid_validation"] += 1
                if tc.get("status") == "error" or tc.get("validation_status") == "INVALID" or tc.get("has_error"):
                    tool_invocations[tname]["failures"] += 1
                    if tname in task_failed_tools:
                        repeated_failure_calls[tname] += 1
                    task_failed_tools.add(tname)

        summary = {}
        for tname, stats in tool_invocations.items():
            inv = stats["invocations"]
            f = stats["failures"]
            summary[tname] = {
                "invocations": inv,
                "failures": f,
                "failure_rate": safe_div(f, inv),
                "perturbed_calls": stats["perturbed_calls"],
                "invalid_validation_count": stats["invalid_validation"],
                "invalid_validation_rate": safe_div(stats["invalid_validation"], inv),
                "repeated_failures": repeated_failure_calls.get(tname, 0)
            }
        return summary

    def _compute_failure_categories(self) -> Dict[str, Any]:
        """Aggregate failure diagnosis categories and failure stages."""
        cat_counts = defaultdict(int)
        stage_counts = defaultdict(int)

        for tr in self.task_records:
            # Check diagnoses
            for d in tr.get("diagnoses", []):
                cat = d.get("category", "unclassified")
                cat_counts[cat] += 1

            # Check task failure reason / stage
            if tr.get("passed") is False:
                fr = str(tr.get("failure_reason", "")).lower()
                if "trace" in fr or "tool" in fr:
                    stage_counts["tool_execution"] += 1
                elif "semantic" in fr or "validation" in fr:
                    stage_counts["semantic_validation"] += 1
                elif "budget" in fr or "abort" in fr or "loop" in fr:
                    stage_counts["recovery_controller"] += 1
                elif "judge" in fr or "eval" in fr:
                    stage_counts["task_judgement"] += 1
                else:
                    stage_counts["unspecified_failure"] += 1

        return {
            "diagnosis_categories": dict(cat_counts),
            "failure_stages": dict(stage_counts)
        }

    def _compute_recovery_analysis(self) -> Dict[str, Any]:
        """Compute recovery success rates, budget exhaustion, and DAG reroute outcomes."""
        total_recovery_directives = defaultdict(int)
        total_recovery_attempts = 0
        budget_exhaustions = 0
        loop_detections = 0
        successful_recoveries = 0

        dag_selections = 0
        dag_pruned = 0

        for tr in self.task_records:
            recs = tr.get("recovery_events", [])
            total_recovery_attempts += len(recs)
            for r in recs:
                act = r.get("action", "unknown")
                total_recovery_directives[act] += 1
                if "exhausted" in str(r.get("rationale", "")).lower():
                    budget_exhaustions += 1
                if r.get("loop_warning"):
                    loop_detections += 1

            if recs and tr.get("passed") is True:
                successful_recoveries += 1

            for dag in tr.get("dag_decisions", []):
                if dag.get("is_viable"):
                    dag_selections += 1
                else:
                    dag_pruned += 1

        tasks_with_recovery = sum(1 for tr in self.task_records if tr.get("recovery_events"))

        return {
            "total_recovery_attempts": total_recovery_attempts,
            "tasks_attempting_recovery": tasks_with_recovery,
            "tasks_successfully_recovered": successful_recoveries,
            "recovery_success_rate": safe_div(successful_recoveries, tasks_with_recovery),
            "directives_breakdown": dict(total_recovery_directives),
            "budget_exhaustion_count": budget_exhaustions,
            "loop_deadlock_count": loop_detections,
            "dag_path_selected_count": dag_selections,
            "dag_path_pruned_count": dag_pruned
        }

    def _compute_agent_comparison(self) -> Dict[str, Any]:
        """Compare Baseline versus CARE agents on matched tasks where available."""
        by_agent: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "tasks": {},
            "total": 0,
            "passed": 0,
            "tokens": [],
            "durations": []
        })

        for tr in self.task_records:
            agent = tr.get("agent_type", "unknown").lower()
            tid = tr.get("task_id")
            mode = tr.get("mode", "P0")
            key = f"{tid}_{mode}"

            by_agent[agent]["tasks"][key] = tr.get("passed") is True
            by_agent[agent]["total"] += 1
            if tr.get("passed") is True:
                by_agent[agent]["passed"] += 1

            tok = extract_tokens(tr)
            if tok:
                by_agent[agent]["tokens"].append(tok)

        # Matched comparison
        agents = list(by_agent.keys())
        matched_summary = {}
        if len(agents) >= 2:
            a1, a2 = agents[0], agents[1]
            shared_keys = set(by_agent[a1]["tasks"].keys()) & set(by_agent[a2]["tasks"].keys())
            if shared_keys:
                a1_pass = sum(1 for k in shared_keys if by_agent[a1]["tasks"][k])
                a2_pass = sum(1 for k in shared_keys if by_agent[a2]["tasks"][k])
                matched_summary = {
                    "matched_tasks_count": len(shared_keys),
                    f"{a1}_matched_tsr": safe_div(a1_pass, len(shared_keys)),
                    f"{a2}_matched_tsr": safe_div(a2_pass, len(shared_keys)),
                    "delta_tsr": safe_div(a2_pass - a1_pass, len(shared_keys))
                }

        overview = {}
        for ag, st in by_agent.items():
            tot = st["total"]
            overview[ag] = {
                "total": tot,
                "passed": st["passed"],
                "tsr": safe_div(st["passed"], tot),
                "mean_tokens": statistics.mean(st["tokens"]) if st["tokens"] else 0.0
            }

        return {
            "overview": overview,
            "matched_comparison": matched_summary
        }

    def _compute_diagnostic_metrics(self) -> Dict[str, Any]:
        """Compute the recommended additional Section 12 diagnostic metrics."""
        total_tasks = len(self.task_records)
        perturbed_tasks = [tr for tr in self.task_records if tr.get("mode") != "P0"]
        total_perturbed = len(perturbed_tasks)

        # 1. Perturbation activation rate
        activated_tasks = [tr for tr in perturbed_tasks if tr.get("perturbation_tracking", {}).get("activations")]
        activation_rate = safe_div(len(activated_tasks), total_perturbed)

        # 2. Perturbation recovery rate
        recovered_tasks = [tr for tr in activated_tasks if tr.get("passed") is True]
        prr = safe_div(len(recovered_tasks), len(activated_tasks))

        # 3. Uncertain attribution rate
        uncertain_tasks = [
            tr for tr in self.task_records
            if tr.get("causal_attribution", {}).get("attribution") == CausalAttribution.CHANGED_FAILURE_UNCERTAIN.value
        ]
        uncertain_rate = safe_div(len(uncertain_tasks), total_tasks)

        # 4. Telemetry completeness rate (records containing tool_calls and status)
        complete_records = [
            tr for tr in self.task_records
            if "tool_calls" in tr and "causal_attribution" in tr and "passed" in tr
        ]
        completeness_rate = safe_div(len(complete_records), total_tasks)

        # 5. Semantic invalid output rate across all tool calls
        total_calls = 0
        invalid_calls = 0
        for tr in self.task_records:
            for tc in tr.get("tool_calls", []):
                total_calls += 1
                if tc.get("validation_status") == "INVALID":
                    invalid_calls += 1
        semantic_invalid_rate = safe_div(invalid_calls, total_calls)

        return {
            "perturbation_activation_rate": {
                "numerator": len(activated_tasks),
                "denominator": total_perturbed,
                "rate": activation_rate
            },
            "perturbation_recovery_rate": {
                "numerator": len(recovered_tasks),
                "denominator": len(activated_tasks),
                "rate": prr
            },
            "uncertain_attribution_rate": {
                "numerator": len(uncertain_tasks),
                "denominator": total_tasks,
                "rate": uncertain_rate
            },
            "telemetry_completeness_rate": {
                "numerator": len(complete_records),
                "denominator": total_tasks,
                "rate": completeness_rate
            },
            "semantic_invalid_output_rate": {
                "numerator": invalid_calls,
                "denominator": total_calls,
                "rate": semantic_invalid_rate
            }
        }

    def _export_csvs(self, report: Dict[str, Any]) -> None:
        """Export tabular comparison CSV files."""
        # 1. failure_analysis.csv
        fa_csv = self.output_dir / "failure_analysis.csv"
        with open(fa_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["task_id", "mode", "complexity", "agent_type", "model", "passed", "attribution", "attribution_confidence", "failed_tools", "failure_reason"])
            for tr in self.task_records:
                ca = tr.get("causal_attribution", {})
                w.writerow([
                    tr.get("task_id"),
                    tr.get("mode"),
                    tr.get("complexity"),
                    tr.get("agent_type"),
                    tr.get("model"),
                    tr.get("passed"),
                    ca.get("attribution"),
                    ca.get("confidence"),
                    ";".join(tr.get("failed_tools", [])),
                    str(tr.get("failure_reason", "")).replace("\n", " ")[:200]
                ])

        # 2. perturbation_comparison.csv
        pc_csv = self.output_dir / "perturbation_comparison.csv"
        with open(pc_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["attribution_category", "count", "total_sample", "rate"])
            for cat, data in report["causal_attribution"]["attribution_breakdown"].items():
                w.writerow([cat, data["count"], data["total"], f"{data['rate']:.4f}"])

        # 3. tool_failure_summary.csv
        tf_csv = self.output_dir / "tool_failure_summary.csv"
        with open(tf_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tool_name", "invocations", "failures", "failure_rate", "perturbed_calls", "invalid_validation_count", "invalid_validation_rate", "repeated_failures"])
            for tname, stats in report["tool_failures"].items():
                w.writerow([
                    tname,
                    stats["invocations"],
                    stats["failures"],
                    f"{stats['failure_rate']:.4f}",
                    stats["perturbed_calls"],
                    stats["invalid_validation_count"],
                    f"{stats['invalid_validation_rate']:.4f}",
                    stats["repeated_failures"]
                ])

        # 4. recovery_summary.csv
        rec_csv = self.output_dir / "recovery_summary.csv"
        with open(rec_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["metric", "value"])
            rec = report["recovery_analysis"]
            w.writerow(["total_recovery_attempts", rec["total_recovery_attempts"]])
            w.writerow(["tasks_attempting_recovery", rec["tasks_attempting_recovery"]])
            w.writerow(["tasks_successfully_recovered", rec["tasks_successfully_recovered"]])
            w.writerow(["recovery_success_rate", f"{rec['recovery_success_rate']:.4f}"])
            w.writerow(["budget_exhaustion_count", rec["budget_exhaustion_count"]])
            w.writerow(["loop_deadlock_count", rec["loop_deadlock_count"]])
            for directive, count in rec["directives_breakdown"].items():
                w.writerow([f"directive_{directive}", count])

        # 5. path_analysis.csv
        path_csv = self.output_dir / "path_analysis.csv"
        with open(path_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["task_id", "mode", "failed_tool", "selected_tool", "is_viable", "reason", "target_path"])
            for tr in self.task_records:
                for dag in tr.get("dag_decisions", []):
                    w.writerow([
                        tr.get("task_id"),
                        tr.get("mode"),
                        dag.get("failed_tool"),
                        dag.get("selected_tool"),
                        dag.get("is_viable"),
                        dag.get("reason"),
                        ";".join(dag.get("target_path", []) or [])
                    ])

        # 6. metric_comparison.csv
        mc_csv = self.output_dir / "metric_comparison.csv"
        with open(mc_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["dimension", "key", "total", "passed", "failed", "tsr", "mean_tokens"])
            for m, s in report["metrics"]["by_mode"].items():
                w.writerow(["mode", m, s["total"], s["passed"], s["failed"], f"{s['tsr']:.4f}", f"{s['mean_tokens']:.1f}"])
            for c, s in report["metrics"]["by_complexity"].items():
                w.writerow(["complexity", c, s["total"], s["passed"], s["failed"], f"{s['tsr']:.4f}", "N/A"])

    def _export_json(self, report: Dict[str, Any]) -> None:
        """Export comprehensive JSON summary."""
        json_file = self.output_dir / "failure_analysis.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _export_markdown_report(self, report: Dict[str, Any]) -> None:
        """Generate human-readable Markdown summary report."""
        md_file = self.output_dir / "failure_analysis_report.md"
        lines = []
        lines.append("# ToolMaze Offline Failure Analysis & Diagnostic Report")
        lines.append("")
        lines.append(f"- **Generated At**: {report['generated_at']}")
        lines.append(f"- **Runs Analyzed**: `{', '.join(report['runs_analyzed'])}`")
        lines.append(f"- **Total Tasks Analyzed**: {report['total_tasks_analyzed']}")
        lines.append(f"- **Schema Version**: `{report['schema_version']}`")
        lines.append("")

        lines.append("## 1. Task Success Rate (TSR) by Perturbation Mode")
        lines.append("| Mode | Total | Passed | Failed | TSR | Mean Tokens | Mean Duration (s) |")
        lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
        for m, s in report["metrics"]["by_mode"].items():
            lines.append(f"| {m} | {s['total']} | {s['passed']} | {s['failed']} | **{s['tsr']*100:.1f}%** | {s['mean_tokens']:.0f} | {s['mean_duration_sec']:.2f} |")
        lines.append("")

        lines.append("## 2. Causal Attribution of Failures")
        lines.append("| Causal Category | Count | Sample Size | Proportion |")
        lines.append("| :--- | :---: | :---: | :---: |")
        for cat, d in report["causal_attribution"]["attribution_breakdown"].items():
            lines.append(f"| `{cat}` | {d['count']} | {d['total']} | {d['rate']*100:.1f}% |")
        lines.append("")

        cfg_act = report["causal_attribution"]["configured_vs_activated"]
        lines.append(f"- **Total Configured Perturbations**: {cfg_act['total_configured_perturbations']}")
        lines.append(f"- **Total Actually Activated Perturbations**: {cfg_act['total_activated_perturbations']}")
        lines.append(f"- **Tasks Recovered After Activation**: {cfg_act['tasks_recovered']}")
        lines.append("")

        lines.append("## 3. Agent Performance Comparison (Baseline vs CARE)")
        comp = report["baseline_vs_care"]["overview"]
        lines.append("| Agent | Total | Passed | TSR | Mean Tokens |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")
        for ag, st in comp.items():
            lines.append(f"| `{ag}` | {st['total']} | {st['passed']} | **{st['tsr']*100:.1f}%** | {st['mean_tokens']:.0f} |")
        lines.append("")

        matched = report["baseline_vs_care"]["matched_comparison"]
        if matched:
            lines.append("### Matched Task Comparison")
            for k, v in matched.items():
                if isinstance(v, float):
                    lines.append(f"- **{k}**: {v*100:.2f}%")
                else:
                    lines.append(f"- **{k}**: {v}")
            lines.append("")

        lines.append("## 4. Recovery and DAG Rerouting Summary")
        rec = report["recovery_analysis"]
        lines.append(f"- **Total Recovery Directives Issued**: {rec['total_recovery_attempts']}")
        lines.append(f"- **Tasks Attempting Recovery**: {rec['tasks_attempting_recovery']}")
        lines.append(f"- **Tasks Successfully Recovered**: {rec['tasks_successfully_recovered']} ({rec['recovery_success_rate']*100:.1f}%)")
        lines.append(f"- **Budget Exhaustions**: {rec['budget_exhaustion_count']}")
        lines.append(f"- **Loop / Cyclic Deadlocks Prevented**: {rec['loop_deadlock_count']}")
        lines.append(f"- **Alternative DAG Paths Selected**: {rec['dag_path_selected_count']} (Pruned: {rec['dag_path_pruned_count']})")
        lines.append("")

        lines.append("## 5. Diagnostic Metrics (Section 12)")
        diag = report["diagnostic_metrics"]
        lines.append(f"- **Perturbation Activation Rate**: {diag['perturbation_activation_rate']['rate']*100:.1f}% ({diag['perturbation_activation_rate']['numerator']}/{diag['perturbation_activation_rate']['denominator']})")
        lines.append(f"- **Perturbation Recovery Rate (PRR)**: {diag['perturbation_recovery_rate']['rate']*100:.1f}% ({diag['perturbation_recovery_rate']['numerator']}/{diag['perturbation_recovery_rate']['denominator']})")
        lines.append(f"- **Rate of Failures with Uncertain Attribution**: {diag['uncertain_attribution_rate']['rate']*100:.1f}% ({diag['uncertain_attribution_rate']['numerator']}/{diag['uncertain_attribution_rate']['denominator']})")
        lines.append(f"- **Semantic Invalid Output Rate**: {diag['semantic_invalid_output_rate']['rate']*100:.1f}% ({diag['semantic_invalid_output_rate']['numerator']}/{diag['semantic_invalid_output_rate']['denominator']})")
        lines.append(f"- **Telemetry Completeness Rate**: {diag['telemetry_completeness_rate']['rate']*100:.1f}% ({diag['telemetry_completeness_rate']['numerator']}/{diag['telemetry_completeness_rate']['denominator']})")
        lines.append("")

        with open(md_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="ToolMaze Offline Failure Analysis and Experiment Comparison Pipeline")
    parser.add_argument("--records-dir", type=str, default="evaluation/experiment_records",
                        help="Base directory containing saved run folders")
    parser.add_argument("--run-id", type=str, default=None,
                        help="Specific run ID to analyze")
    parser.add_argument("--run-ids", nargs="+", default=None,
                        help="List of run IDs to aggregate")
    parser.add_argument("--categories", nargs="+", default=None,
                        help="Filter by complexity categories (e.g. C1 C2)")
    parser.add_argument("--modes", nargs="+", default=None,
                        help="Filter by perturbation modes (e.g. P0 P1 P2 P3 P4)")
    parser.add_argument("--task-ids", nargs="+", default=None,
                        help="Filter by specific task IDs")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Filter by model names")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Target output directory for analysis artifacts")

    args = parser.parse_args()

    # Resolve records dir
    rdir = Path(args.records_dir)
    if not rdir.is_absolute():
        rdir = PROJECT_ROOT / rdir

    out_dir = Path(args.output_dir) if args.output_dir else None
    if out_dir and not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir

    run_ids = []
    if args.run_id:
        run_ids.append(args.run_id)
    if args.run_ids:
        run_ids.extend(args.run_ids)

    analyzer = ExperimentAnalyzer(
        records_dir=rdir,
        run_ids=run_ids if run_ids else None,
        categories=args.categories,
        modes=args.modes,
        task_ids=args.task_ids,
        models=args.models,
        output_dir=out_dir
    )

    analyzer.load_records()
    report = analyzer.run_analysis()

    print("\n" + "=" * 60)
    print("OFFLINE FAILURE ANALYSIS COMPLETE")
    print(f"Output files generated in: {analyzer.output_dir}")
    print("=" * 60)
    print(f"- failure_analysis.json")
    print(f"- failure_analysis.csv")
    print(f"- perturbation_comparison.csv")
    print(f"- tool_failure_summary.csv")
    print(f"- recovery_summary.csv")
    print(f"- path_analysis.csv")
    print(f"- metric_comparison.csv")
    print(f"- failure_analysis_report.md")


if __name__ == "__main__":
    main()
