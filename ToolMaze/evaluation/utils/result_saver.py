"""Result Saver for storing evaluation outputs."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from evaluation.utils.trace_logger import TraceLogger


class ResultSaver:
    """Manages saving of evaluation results to disk."""

    def __init__(
        self,
        base_dir: str = "evaluation/results",
        model: str = "unknown",
        agent_type: str = "fc",
        task_category: str = "c1"
    ):
        """Initialize result saver.

        Args:
            base_dir: Base directory for saving results
            model: Model name (e.g., "gpt-4o", "claude-3")
            agent_type: Agent type - "fc" (function calling) or "mcp"
            task_category: Task category (e.g., "c1", "c2")
        """
        # 清理模型名中的非法文件系统字符
        safe_model = model.replace("/", "_").replace(":", "_")

        self.output_dir = Path(base_dir) / safe_model / agent_type / task_category

        # 分目录存储推理、评测、指标与报告
        self.inferences_dir = self.output_dir / "inferences"
        self.evaluations_dir = self.output_dir / "evaluations"
        self.metrics_dir = self.output_dir / "metrics"
        self.reports_dir = self.output_dir / "reports"

        # 创建所需目录
        for directory in [
            self.inferences_dir,
            self.evaluations_dir,
            self.metrics_dir,
            self.reports_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def save_inference(
        self,
        task_id: str,
        mode: str,
        trace_logger: "TraceLogger",
        token_usage: Dict[str, int]
    ) -> Path:
        """Save inference trace (without judgement).

        Args:
            task_id: Task identifier
            mode: Perturbation mode
            trace_logger: TraceLogger instance
            token_usage: Token usage dict

        Returns:
            Path to saved file
        """
        filename = f"{task_id}_{mode}_inference.json"
        filepath = self.inferences_dir / filename

        # 仅保存推理数据（不含评测结果）
        inference_data = trace_logger.to_dict(token_usage=token_usage, judgement=None)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(inference_data, f, indent=2, ensure_ascii=False)

        return filepath

    def save_evaluation(
        self,
        task_id: str,
        mode: str,
        judgement: Dict[str, Any]
    ) -> Path:
        """Save evaluation result (judgement only).

        Args:
            task_id: Task identifier
            mode: Perturbation mode
            judgement: Judgement data

        Returns:
            Path to saved file
        """
        filename = f"{task_id}_{mode}_eval.json"
        filepath = self.evaluations_dir / filename

        # 组装评测数据并保存
        eval_data = {
            "task_id": task_id,
            "mode": mode,
            **judgement
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(eval_data, f, indent=2, ensure_ascii=False)

        return filepath

    def save_trace(
        self,
        task_id: str,
        mode: str,
        trace_logger: "TraceLogger",
        token_usage: Dict[str, int],
        judgement: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Save execution trace by saving inference and evaluation separately.

        Args:
            task_id: Task identifier
            mode: Perturbation mode
            trace_logger: TraceLogger instance
            token_usage: Token usage dict
            judgement: Optional judgement data

        Returns:
            Path to saved inference file
        """
        # 分别保存推理与评测结果
        inference_path = self.save_inference(task_id, mode, trace_logger, token_usage)

        # 若提供了 judgement 则额外保存评测文件
        if judgement:
            self.save_evaluation(task_id, mode, judgement)

        return inference_path

    def save_metrics(self, metrics_report: Dict[str, Any]) -> Path:
        """Save metrics report.

        Args:
            metrics_report: Metrics data

        Returns:
            Path to saved file
        """
        # 使用时间戳命名避免覆盖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_report_{timestamp}.json"
        filepath = self.metrics_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metrics_report, f, indent=2, ensure_ascii=False)

        return filepath

    def save_report(self, report_name: str, content: str) -> Path:
        """Save text report.

        Args:
            report_name: Name of the report
            content: Report content

        Returns:
            Path to saved file
        """
        # 使用时间戳命名避免覆盖
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_name}_{timestamp}.txt"
        filepath = self.reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def inference_exists(self, task_id: str, mode: str) -> bool:
        """Check if inference file exists.

        Args:
            task_id: Task identifier
            mode: Perturbation mode

        Returns:
            True if inference file exists
        """
        filename = f"{task_id}_{mode}_inference.json"
        filepath = self.inferences_dir / filename
        # 直接检查文件是否存在
        return filepath.exists()

    def load_inference(self, task_id: str, mode: str) -> Dict[str, Any]:
        """Load inference trace.

        Args:
            task_id: Task identifier
            mode: Perturbation mode

        Returns:
            Inference data
        """
        filename = f"{task_id}_{mode}_inference.json"
        filepath = self.inferences_dir / filename

        # 读取并返回推理 JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_evaluation(self, task_id: str, mode: str) -> Dict[str, Any]:
        """Load evaluation result.

        Args:
            task_id: Task identifier
            mode: Perturbation mode

        Returns:
            Evaluation data
        """
        filename = f"{task_id}_{mode}_eval.json"
        filepath = self.evaluations_dir / filename

        # 读取并返回评测 JSON
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_completed_tasks(self) -> list[tuple]:
        """Return (task_id, mode) pairs that have both inference and evaluation on disk.

        Returns:
            List of (task_id, mode) tuples
        """
        completed = []
        for eval_file in sorted(self.evaluations_dir.glob("*_eval.json")):
            stem = eval_file.stem  # e.g. "C3_task_009_P2_eval"
            # 去掉末尾 "_eval"
            name = stem[: -len("_eval")]
            # 最后一段为 mode (P0..P4)
            parts = name.rsplit("_", 1)
            if len(parts) != 2:
                continue
            task_id, mode = parts
            # 仅当对应推理文件也存在时才视为完成
            if self.inference_exists(task_id, mode):
                completed.append((task_id, mode))
        return completed
