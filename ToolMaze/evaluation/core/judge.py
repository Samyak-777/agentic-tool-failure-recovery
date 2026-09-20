"""Judge System for evaluating agent performance based on ground truth.

重构版本：使用子集匹配评估算法。

评估逻辑：
- 检查 Agent 的执行轨迹是否覆盖了 Expected Result
- 工具覆盖：Agent 必须调用 Expected Result 中出现的所有工具
- 调用次数：Agent 的调用次数 >= Expected Result 中的次数
- 执行顺序：不检查，Agent 可以按任意顺序执行

Implements the decision logic matrix:
- P0: Standard execution, must succeed
- P1: Must succeed with retry
- P2: Must fail gracefully at victim node
- P3: Must succeed with data validation and retry
- P4: Must fail gracefully after detecting data corruption
"""

import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Any, Optional, List, Set


class JudgeSystem:
    """Judge system for evaluating agent execution traces using subset matching."""

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        template_dir: Optional[str] = None
    ):
        """Initialize judge system.

        Args:
            llm_client: LLM client for semantic judgement (OpenAI client)
            model: Model name for LLM-as-judge
            temperature: Sampling temperature
            template_dir: Base directory containing template folders
        """
        self.llm_client = llm_client
        self.model = model
        self.temperature = temperature
        self.template_dir = template_dir

    def judge(self, task_json: Dict[str, Any], trace: Dict[str, Any]) -> Dict[str, Any]:
        """Judge whether the agent execution passed or failed.

        Args:
            task_json: Task specification with expected_result and execution_trace
            trace: Execution trace from sandbox

        Returns:
            Judgement result with pass/fail and detailed reasoning
        """
        mode = task_json.get("perturbation_mode", "P0")
        complexity = task_json.get("complexity", "C1")

        # 按复杂度分派到对应评测逻辑
        if complexity == "C2":
            return self._judge_c2(task_json, trace, mode)
        if complexity == "C3":
            return self._judge_c3(task_json, trace, mode)
        if complexity == "C4":
            return self._judge_c4(task_json, trace, mode)

        # C1: 按扰动模式选择评测逻辑
        if mode == "P0":
            return self._check_p0_legacy(task_json, trace)
        elif mode == "P1":
            return self._check_p1_legacy(task_json, trace)
        elif mode == "P2":
            return self._check_p2_legacy(task_json, trace)
        elif mode == "P3":
            return self._check_p3_legacy(task_json, trace)
        elif mode == "P4":
            return self._check_p4_legacy(task_json, trace)
        else:
            return {
                "pass": False,
                "failure_reason": f"Unknown mode: {mode}",
                "trace_check": {},
            }

    def _is_structured_expected_result(self, expected_result: Any) -> bool:
        """检查 expected_result 是否为新的结构化格式"""
        return (
            isinstance(expected_result, dict) and
            "tool_calls" in expected_result and
            isinstance(expected_result["tool_calls"], list)
        )

    def _check_subset_matching(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """使用子集匹配算法评估 Agent 执行轨迹

        核心逻辑：
        1. 工具覆盖：Agent 必须调用 Expected Result 中的所有工具
        2. 调用次数：Agent 的调用次数 >= Expected Result 中的次数
        3. 顺序无关：不检查执行顺序
        """
        expected_result = task_json.get("expected_result", {})
        expected_tool_calls = expected_result.get("tool_calls", [])

        # 提取期望调用的工具列表
        expected_tools = [call["tool_name"] for call in expected_tool_calls]

        # 提取实际执行轨迹中的工具列表
        actual_trace = self._extract_actual_trace(trace)

        # 执行子集匹配检查
        subset_result = self._evaluate_subset_matching(expected_tools, actual_trace)

        # 定位 victim tool（若存在）
        victim_tool = self._find_victim_tool(task_json)

        # 组装 trace_check 结果
        trace_check = {
            "match": subset_result["pass"],
            "victim_tool": victim_tool,
            "missing_tools": subset_result["missing_tools"],
            "insufficient_calls": subset_result["insufficient_calls"],
            "tool_call_counts": subset_result["tool_call_counts"],
            "ground_truth": {"execution_trace": expected_tools},
            "actual": {"execution_trace": actual_trace}
        }

        # 收集失败原因
        failure_reasons = []
        if subset_result["missing_tools"]:
            failure_reasons.append(f"missing tools: {subset_result['missing_tools']}")
        if subset_result["insufficient_calls"]:
            for tool, info in subset_result["insufficient_calls"].items():
                failure_reasons.append(
                    f"'{tool}' called {info['actual']} times, expected >= {info['expected']}"
                )

        passed = subset_result["pass"]

        return {
            "pass": passed,
            "failure_reason": None if passed else f"{mode} failed: {'; '.join(failure_reasons)}",
            "trace_check": trace_check,

        }

    def _evaluate_subset_matching(
        self,
        expected_tools: List[str],
        agent_tools: List[str]
    ) -> Dict[str, Any]:
        """执行子集匹配评估

        检查两个条件：
        1. 工具覆盖：Agent 是否调用了 Expected Result 中的所有工具？
        2. 调用次数：Agent 对每个工具的调用次数是否 >= Expected Result 中的次数？

        注意：不检查执行顺序
        """
        # 1. 检查工具覆盖：期望工具是否全部出现
        expected_tool_set = set(expected_tools)
        agent_tool_set = set(agent_tools)
        missing_tools = list(expected_tool_set - agent_tool_set)

        # 2. 检查工具调用次数：实际次数是否不少于期望次数
        expected_counts = Counter(expected_tools)
        agent_counts = Counter(agent_tools)

        insufficient_calls = {}
        for tool, expected_count in expected_counts.items():
            agent_count = agent_counts.get(tool, 0)
            if agent_count < expected_count:
                insufficient_calls[tool] = {
                    "expected": expected_count,
                    "actual": agent_count
                }

        # 3. 综合判定：无缺失工具且调用次数均达标
        pass_check = (len(missing_tools) == 0) and (len(insufficient_calls) == 0)

        return {
            "pass": pass_check,
            "missing_tools": missing_tools,
            "insufficient_calls": insufficient_calls,
            "tool_call_counts": {
                "expected": dict(expected_counts),
                "actual": dict(agent_counts)
            }
        }

    # ========== Legacy Mode-Specific Checkers (for backward compatibility) ==========

    def _check_p0_legacy(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check P0 (Ideal/Baseline): Must succeed with standard execution.

        Legacy version for backward compatibility with old expected_result format.
        """
        # Extract traces
        ground_truth_trace = self._extract_ground_truth_trace(task_json)
        actual_trace = self._extract_actual_trace(trace)

        required_tools = set(ground_truth_trace)
        successful_tools = self._extract_successful_tools(trace)
        missing_tools = list(required_tools - successful_tools)
        all_tools_executed = len(missing_tools) == 0

        trace_check = {
            "match": all_tools_executed,
            "victim_tool": None,
            "missing_tools": missing_tools,
            "ground_truth": {"execution_trace": ground_truth_trace},
            "actual": {"execution_trace": actual_trace}
        }

        passed = all_tools_executed
        failure_reasons = []
        if missing_tools:
            failure_reasons.append(f"missing required tools: {missing_tools}")

        return {
            "pass": passed,
            "failure_reason": None if passed else f"P0 failed: {'; '.join(failure_reasons)}",
            "trace_check": trace_check,

        }

    def _check_p1_legacy(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check P1 (Explicit-Transient): Must succeed with retry.

        Legacy version for backward compatibility.
        """
        victim_tool = self._find_victim_tool(task_json)
        ground_truth_trace = self._extract_ground_truth_trace(task_json)
        actual_trace = self._extract_actual_trace(trace)
        retry_info = self._check_retry(trace, victim_tool)

        required_tools = set(ground_truth_trace)
        successful_tools = self._extract_successful_tools(trace)
        missing_tools = list(required_tools - successful_tools)

        trace_match = retry_info["has_retry"] and retry_info["final_success"]
        trace_check = {
            "match": trace_match,
            "victim_tool": victim_tool,
            "missing_tools": missing_tools,
            "ground_truth": {"execution_trace": ground_truth_trace},
            "actual": {"execution_trace": actual_trace}
        }

        passed = trace_match and len(missing_tools) == 0
        failure_reasons = []
        if not retry_info["has_retry"]:
            failure_reasons.append(f"no retry on '{victim_tool}' (called {retry_info['call_count']} time(s), need >=2)")
        if not retry_info["final_success"]:
            failure_reasons.append(f"'{victim_tool}' never succeeded after retries")
        if missing_tools:
            failure_reasons.append(f"missing required tools: {missing_tools}")

        return {
            "pass": passed,
            "failure_reason": None if passed else f"P1 failed: {'; '.join(failure_reasons)}",
            "trace_check": trace_check,

        }

    def _check_p2_legacy(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check P2 (Explicit-Permanent): Must fail gracefully.

        Pass condition:
        1. All pre-victim tools successfully called.
        2. Victim tool was called (and received perturbed response).
        3. After victim: only victim itself may be retried; no other tool calls allowed.
        """
        victim_tool = self._find_victim_tool(task_json)
        actual_trace = self._extract_actual_trace(trace)

        # 使用 P2/P4 通用停损检查
        trace_check = self._check_p2_p4_stop_after_victim(
            task_json, actual_trace, victim_tool, trace=trace
        )

        passed = trace_check["match"]
        failure_reasons = []
        if victim_tool in trace_check.get("missing_tools", []):
            failure_reasons.append(f"'{victim_tool}' was never called")
        elif trace_check.get("missing_tools"):
            failure_reasons.append(f"missing required pre-victim tools: {trace_check['missing_tools']}")
        if trace_check.get("forbidden_tools_called"):
            failure_reasons.append(f"agent should have stopped but called other tools after victim: {trace_check['forbidden_tools_called']}")
        if trace_check.get("abort_required") and not trace_check.get("abort_in_final_answer"):
            failure_reasons.append(
                f"'{victim_tool}' is the last node; final_answer must contain an explicit abort signal"
            )

        return {
            "pass": passed,
            "failure_reason": None if passed else f"P2 failed: {'; '.join(failure_reasons)}",
            "trace_check": trace_check,
        }

    def _check_p3_legacy(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check P3 (Implicit-Transient): Same logic as P1.

        P3 is transient — corruption only happens once, retry gets clean data.
        Agent must: retry victim -> get clean data -> complete all required tools.
        """
        victim_tool = self._find_victim_tool(task_json)
        ground_truth_trace = self._extract_ground_truth_trace(task_json)
        actual_trace = self._extract_actual_trace(trace)
        retry_info = self._check_retry(trace, victim_tool)

        required_tools = set(ground_truth_trace)
        successful_tools = self._extract_successful_tools(trace)
        missing_tools = list(required_tools - successful_tools)

        trace_match = retry_info["has_retry"] and retry_info["final_success"]
        trace_check = {
            "match": trace_match,
            "victim_tool": victim_tool,
            "missing_tools": missing_tools,
            "ground_truth": {"execution_trace": ground_truth_trace},
            "actual": {"execution_trace": actual_trace}
        }

        passed = trace_match and len(missing_tools) == 0
        failure_reasons = []
        if not retry_info["has_retry"]:
            failure_reasons.append(f"no retry on '{victim_tool}' (called {retry_info['call_count']} time(s), need >=2)")
        if not retry_info["final_success"]:
            failure_reasons.append(f"'{victim_tool}' never returned clean data after retries")
        if missing_tools:
            failure_reasons.append(f"missing required tools: {missing_tools}")

        return {
            "pass": passed,
            "failure_reason": None if passed else f"P3 failed: {'; '.join(failure_reasons)}",
            "trace_check": trace_check,

        }

    def _check_p4_legacy(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check P4 (Implicit-Permanent): Must fail gracefully after detecting corruption.

        Pass condition:
        1. All pre-victim tools successfully called.
        2. Victim tool was called (and received perturbed/corrupted response).
        3. After victim: only victim itself may be retried; no other tool calls allowed.
        """
        victim_tool = self._find_victim_tool(task_json)
        actual_trace = self._extract_actual_trace(trace)

        # 使用 P2/P4 通用停损检查
        trace_check = self._check_p2_p4_stop_after_victim(
            task_json, actual_trace, victim_tool, trace=trace
        )

        passed = trace_check["match"]
        failure_reasons = []
        if victim_tool in trace_check.get("missing_tools", []):
            failure_reasons.append(f"'{victim_tool}' was never called")
        elif trace_check.get("missing_tools"):
            failure_reasons.append(f"missing required pre-victim tools: {trace_check['missing_tools']}")
        if trace_check.get("forbidden_tools_called"):
            failure_reasons.append(f"agent should have stopped but called other tools after victim: {trace_check['forbidden_tools_called']}")
        if trace_check.get("abort_required") and not trace_check.get("abort_in_final_answer"):
            failure_reasons.append(
                f"'{victim_tool}' is the last node; final_answer must contain an explicit abort signal"
            )

        return {
            "pass": passed,
            "failure_reason": None if passed else f"P4 failed: {'; '.join(failure_reasons)}",
            "trace_check": trace_check,
        }

    # ========== C2 Judge Methods ==========

    def _judge_c2(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C2 统一评测入口。

        C2 的核心语义：模型首次调用某个 alt 工具时触发扰动，
        之后可以重试（P1/P3）或切换到其他 alt 工具（所有 P）。
        """
        # 按模式分派到对应评测逻辑
        if mode == "P0":
            return self._check_c2_p0(task_json, trace)
        elif mode in ("P1", "P3"):
            return self._check_c2_transient(task_json, trace, mode)
        elif mode in ("P2", "P4"):
            return self._check_c2_permanent(task_json, trace, mode)
        return {"pass": False, "failure_reason": f"Unknown mode: {mode}", "trace_check": {}}

    def _check_c2_p0(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """C2 P0: 任意一条路径的所有工具都成功执行即可。"""
        actual_trace = self._extract_actual_trace(trace)
        successful_tools = self._extract_successful_tools(trace)
        # 评估是否存在完整匹配的 valid path
        path_status = self._evaluate_c2_paths(task_json, successful_tools)
        matched_path = path_status["matched_path"]
        missing_tools = [] if matched_path else path_status["closest_missing_tools"]

        if matched_path:
            return {
                "pass": True,
                "failure_reason": None,
                "trace_check": {
                    "match": True,
                    "victim_tool": None,
                    "missing_tools": [],
                    "ground_truth": self._build_c2_ground_truth(task_json),
                    "actual": {"execution_trace": actual_trace}
                }
            }

        return {
            "pass": False,
            "failure_reason": (
                f"C2 P0 failed: no complete path executed successfully; "
                f"missing_tools={missing_tools}"
            ),
            "trace_check": {
                "match": False,
                "victim_tool": None,
                "missing_tools": missing_tools,
                "ground_truth": self._build_c2_ground_truth(task_json),
                "actual": {"execution_trace": actual_trace}
            }
        }

    def _check_c2_transient(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C2 P1/P3: 模型遇到瞬时错误后，重试成功或切换到 alt 工具均算通过。

        通过条件（满足任一）：
        1. 重试：victim tool 被调用 >=2 次且最终成功，任务完成
        2. 切换：调用了另一个 alt 工具且成功，任务完成
        """
        alt_tools = self._get_c2_alt_tools(task_json)
        actual_trace = self._extract_actual_trace(trace)
        successful_tools = self._extract_successful_tools(trace)
        path_status = self._evaluate_c2_paths(task_json, successful_tools)
        ground_truth = self._build_c2_ground_truth(task_json)
        shared_tools = self._get_c2_shared_tools(task_json)
        shared_missing = sorted(shared_tools - successful_tools)

        # 定位首个被调用的 alt 工具作为 victim
        victim_tool = self._find_first_alt_tool_called(trace, alt_tools)
        if not victim_tool:
            return {
                "pass": False,
                "failure_reason": f"{mode} failed: no alternative tool was called",
                "trace_check": {
                    "match": False,
                    "victim_tool": None,
                    "missing_tools": path_status["closest_missing_tools"],
                    "ground_truth": ground_truth,
                    "actual": {"execution_trace": actual_trace}
                }
            }

        # 策略1: 重试通过 — victim 调用 >=2 次且最终成功
        retry_info = self._check_retry(trace, victim_tool)
        retry_pass = retry_info["has_retry"] and retry_info["final_success"]

        # 策略2: 切换通过 — 调用了其他 alt 工具且成功
        other_alt_success = any(
            t in successful_tools for t in alt_tools if t != victim_tool
        )

        # 两种策略都要求共享工具全部成功
        shared_ok = len(shared_missing) == 0

        passed = shared_ok and (retry_pass or other_alt_success)
        missing_tools = [] if passed else path_status["closest_missing_tools"]

        failure_reasons = []
        if not shared_ok:
            failure_reasons.append(f"missing shared tools: {shared_missing}")
        if not retry_pass and not other_alt_success:
            failure_reasons.append(
                f"'{victim_tool}' failed but agent neither retried "
                f"(calls={retry_info['call_count']}) nor switched to alt tool"
            )

        return {
            "pass": passed,
            "failure_reason": None if passed else f"{mode} failed: {'; '.join(failure_reasons)}",
            "trace_check": {
                "match": passed,
                "victim_tool": victim_tool,
                "missing_tools": missing_tools,
                "ground_truth": ground_truth,
                "actual": {"execution_trace": actual_trace}
            }
        }

    def _check_c2_permanent(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C2 P2/P4: 模型遇到永久错误后，必须切换到其他 alt 工具完成任务。

        通过条件：
        1. victim tool 被调用过（触发了扰动）
        2. 调用了另一个 alt 工具且成功
        3. 共享工具全部成功
        """
        alt_tools = self._get_c2_alt_tools(task_json)
        actual_trace = self._extract_actual_trace(trace)
        successful_tools = self._extract_successful_tools(trace)
        path_status = self._evaluate_c2_paths(task_json, successful_tools)
        ground_truth = self._build_c2_ground_truth(task_json)
        shared_tools = self._get_c2_shared_tools(task_json)
        shared_missing = sorted(shared_tools - successful_tools)

        # 定位首个被调用的 alt 工具作为 victim
        victim_tool = self._find_first_alt_tool_called(trace, alt_tools)
        if not victim_tool:
            return {
                "pass": False,
                "failure_reason": f"{mode} failed: no alternative tool was called",
                "trace_check": {
                    "match": False,
                    "victim_tool": None,
                    "missing_tools": path_status["closest_missing_tools"],
                    "ground_truth": ground_truth,
                    "actual": {"execution_trace": actual_trace}
                }
            }

        # 必须切换到其他 alt 工具且成功
        other_alt_success = any(
            t in successful_tools for t in alt_tools if t != victim_tool
        )
        shared_ok = len(shared_missing) == 0

        passed = shared_ok and other_alt_success
        missing_tools = [] if passed else path_status["closest_missing_tools"]

        failure_reasons = []
        if not shared_ok:
            failure_reasons.append(f"missing shared tools: {shared_missing}")
        if not other_alt_success:
            failure_reasons.append(
                f"'{victim_tool}' permanently failed but agent did not switch to alt tool"
            )

        return {
            "pass": passed,
            "failure_reason": None if passed else f"{mode} failed: {'; '.join(failure_reasons)}",
            "trace_check": {
                "match": passed,
                "victim_tool": victim_tool,
                "missing_tools": missing_tools,
                "ground_truth": ground_truth,
                "actual": {"execution_trace": actual_trace}
            }
        }

    def _find_first_alt_tool_called(
        self, trace: Dict[str, Any], alt_tools: Set[str]
    ) -> Optional[str]:
        """找到 trace 中第一个被调用的 alt 工具。"""
        for msg in self._get_messages(trace):
            if msg.get("role") == "assistant" and msg.get("type") == "tool_call":
                tool_name = msg.get("tool_call", {}).get("name")
                if tool_name in alt_tools:
                    return tool_name
        return None

    def _infer_c2_alt_tools_from_paths(self, task_json: Dict[str, Any]) -> Set[str]:
        """从 valid_paths 推导 C2 的替代工具：union(paths) - intersection(paths)。"""
        valid_paths = task_json.get("valid_paths", [])
        if len(valid_paths) < 2:
            return set()

        tool_sets = []
        for vp in valid_paths:
            tools = vp.get("tools", [])
            if isinstance(tools, list):
                tool_sets.append(set(t for t in tools if t))

        if len(tool_sets) < 2:
            return set()

        union_tools = set().union(*tool_sets)
        shared_tools = set.intersection(*tool_sets)
        return union_tools - shared_tools

    def _get_c2_alt_tools(self, task_json: Dict[str, Any]) -> Set[str]:
        """获取 C2 的替代工具集合，优先使用从 valid_paths 推导的结果。"""
        inferred = self._infer_c2_alt_tools_from_paths(task_json)
        if inferred:
            return inferred
        return set(task_json.get("alternative_tools", []))

    def _get_c2_shared_tools(self, task_json: Dict[str, Any]) -> Set[str]:
        """获取 C2 任务中所有路径共享的工具（非 alt 工具）。"""
        alt_tools = self._get_c2_alt_tools(task_json)
        valid_paths = task_json.get("valid_paths", [])
        if not valid_paths:
            return set()
        tool_sets = []
        for vp in valid_paths:
            tools = vp.get("tools", [])
            if isinstance(tools, list):
                tool_sets.append(set(t for t in tools if t))
        if not tool_sets:
            return set()
        shared_tools = set.intersection(*tool_sets)
        return shared_tools - alt_tools

    def _build_c2_ground_truth(self, task_json: Dict[str, Any]) -> Dict[str, Any]:
        """构建 C2 的 ground_truth 展示结构（对齐 C1 的 trace_check 风格）。"""
        valid_paths = task_json.get("valid_paths", [])
        return {
            "valid_paths": [
                {
                    "path_id": vp.get("path_id"),
                    "execution_trace": vp.get("tools", [])
                }
                for vp in valid_paths
            ],
            "alternative_tools": sorted(self._get_c2_alt_tools(task_json))
        }

    def _evaluate_c2_paths(
        self,
        task_json: Dict[str, Any],
        successful_tools: Set[str]
    ) -> Dict[str, Any]:
        """评估 C2 路径匹配情况。

        Returns:
            {
                "matched_path": Optional[str],
                "closest_missing_tools": List[str],
            }
        """
        valid_paths = task_json.get("valid_paths", [])
        if not valid_paths:
            return {
                "matched_path": None,
                "closest_missing_tools": []
            }

        matched_path = None
        closest_missing_tools: Optional[List[str]] = None
        closest_score: Optional[tuple] = None

        for vp in valid_paths:
            required_tools = set(vp.get("tools", []))
            missing = sorted(required_tools - successful_tools)
            path_id = vp.get("path_id")

            if len(missing) == 0 and matched_path is None:
                matched_path = path_id

            score = (len(missing), len(required_tools))
            if closest_score is None or score < closest_score:
                closest_score = score
                closest_missing_tools = missing

        return {
            "matched_path": matched_path,
            "closest_missing_tools": closest_missing_tools or []
        }

    # ========== C3 Judge Methods ==========

    def _judge_c3(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C3 统一评测入口。

        C3 的核心语义：valid_paths 表示完整的 N-to-N 等价可行路径。
        评测必须在"完整路径"粒度上判定是否完成，而不是只看单个 alt tool。
        """
        # 复用 C3/C4 统一的 node-bound 多路径评测逻辑
        return self._judge_node_bound_multi_path(task_json, trace, mode, complexity_label="C3")

    def _judge_c4(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C4 统一评测入口。

        C4 延续 C3 的完整路径评测思路，但扰动目标来自共享 `slot_id`。
        agent 首次命中该 slot 在当前路径上的真实工具时触发扰动。
        """
        # 复用 C3/C4 统一的 node-bound 多路径评测逻辑
        return self._judge_node_bound_multi_path(task_json, trace, mode, complexity_label="C4")

    def _judge_node_bound_multi_path(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str,
        complexity_label: str,
    ) -> Dict[str, Any]:
        """统一处理 C3/C4 的 node-bound 多路径评测。"""
        # 按模式分派到对应评测逻辑
        if mode == "P0":
            return self._check_node_bound_p0(task_json, trace, complexity_label)
        if mode in ("P1", "P3"):
            return self._check_node_bound_transient(task_json, trace, mode, complexity_label)
        if mode in ("P2", "P4"):
            return self._check_node_bound_permanent(task_json, trace, mode, complexity_label)
        return {"pass": False, "failure_reason": f"Unknown mode: {mode}", "trace_check": {}}

    def _check_c3_p0(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """C3 P0: 任意一条完整 valid path 成功即可。"""
        return self._check_node_bound_p0(task_json, trace, complexity_label="C3")

    def _check_node_bound_p0(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        complexity_label: str,
    ) -> Dict[str, Any]:
        """C3/C4 P0: 任意一条完整 valid path 成功即可。"""
        actual_trace = self._extract_actual_trace(trace)
        successful_counts = self._extract_successful_tool_counts(trace)
        # 评估各路径匹配情况
        path_status = self._evaluate_node_bound_paths(task_json, successful_counts)
        matched_paths = path_status["matched_paths"]
        passed = len(matched_paths) > 0

        return {
            "pass": passed,
            "failure_reason": None if passed else (
                f"{complexity_label} P0 failed: no complete valid path executed successfully; "
                f"missing_tools={path_status['closest_missing_tools']}"
            ),
            "trace_check": {
                "match": passed,
                "victim_tool": None,
                "matched_paths": matched_paths,
                "missing_tools": [] if passed else path_status["closest_missing_tools"],
                "insufficient_calls": {} if passed else path_status["closest_insufficient_calls"],
                "ground_truth": self._build_c2_ground_truth(task_json),
                "actual": {"execution_trace": actual_trace}
            }
        }

    def _check_c3_transient(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C3 P1/P3: 模型需要完成一条完整 valid path。

        通过条件（满足任一）：
        1. 重试：在命中的 perturbed path 上重试成功，并完成该完整路径
        2. 切换：切换到不包含 victim tool 的其他完整路径并成功完成
        """
        return self._check_node_bound_transient(task_json, trace, mode, complexity_label="C3")

    def _check_node_bound_transient(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str,
        complexity_label: str,
    ) -> Dict[str, Any]:
        """C3/C4 P1/P3: 需要完成一条完整 valid path。"""
        actual_trace = self._extract_actual_trace(trace)
        successful_counts = self._extract_successful_tool_counts(trace)
        # 评估各路径匹配情况
        path_status = self._evaluate_node_bound_paths(task_json, successful_counts)
        matched_paths = path_status["matched_paths"]
        ground_truth = self._build_node_bound_ground_truth(task_json)

        # 定位首个被调用的扰动候选工具作为 victim
        victim_candidates = self._get_node_bound_perturbed_tools(task_json)
        victim_tool = self._find_first_alt_tool_called(trace, victim_candidates)
        if not victim_tool:
            return {
                "pass": False,
                "failure_reason": f"{mode} failed: no perturbed {complexity_label} entry tool was called",
                "trace_check": {
                    "match": False,
                    "victim_tool": None,
                    "matched_paths": matched_paths,
                    "missing_tools": path_status["closest_missing_tools"],
                    "insufficient_calls": path_status["closest_insufficient_calls"],
                    "ground_truth": ground_truth,
                    "actual": {"execution_trace": actual_trace}
                }
            }

        # 策略1: 在包含 victim 的路径上重试并成功完成
        retry_info = self._check_retry(trace, victim_tool)
        source_paths = self._find_paths_containing_tool(task_json, victim_tool)
        matched_source_paths = [path_id for path_id in matched_paths if path_id in source_paths]
        # 策略2: 切换到不包含 victim 的其他路径并成功完成
        switched_paths = [path_id for path_id in matched_paths if path_id not in source_paths]

        retry_pass = (
            retry_info["has_retry"] and
            retry_info["final_success"] and
            len(matched_source_paths) > 0
        )
        switch_pass = len(switched_paths) > 0
        passed = retry_pass or switch_pass

        failure_reasons = []
        if not matched_paths:
            failure_reasons.append("no complete valid path executed successfully")
        if not retry_pass and not switch_pass:
            if mode == "P3" and retry_info["call_count"] == 1:
                failure_reasons.append(
                    f"Sanity Ignorance - agent used corrupted data from '{victim_tool}' without retry"
                )
            else:
                failure_reasons.append(
                    f"'{victim_tool}' neither led to a completed retried path nor a completed switched path"
                )

        return {
            "pass": passed,
            "failure_reason": None if passed else f"{mode} failed: {'; '.join(failure_reasons)}",
            "trace_check": {
                "match": passed,
                "victim_tool": victim_tool,
                "matched_paths": matched_paths,
                "retry_completed_paths": matched_source_paths,
                "switched_paths": switched_paths,
                "missing_tools": [] if passed else path_status["closest_missing_tools"],
                "insufficient_calls": {} if passed else path_status["closest_insufficient_calls"],
                "ground_truth": ground_truth,
                "actual": {"execution_trace": actual_trace}
            }
        }

    def _check_c3_permanent(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str
    ) -> Dict[str, Any]:
        """C3 P2/P4: 必须切换到其他完整 valid path 才算通过。"""
        return self._check_node_bound_permanent(task_json, trace, mode, complexity_label="C3")

    def _check_node_bound_permanent(
        self,
        task_json: Dict[str, Any],
        trace: Dict[str, Any],
        mode: str,
        complexity_label: str,
    ) -> Dict[str, Any]:
        """C3/C4 P2/P4: 必须切换到其他完整 valid path 才算通过。"""
        actual_trace = self._extract_actual_trace(trace)
        successful_counts = self._extract_successful_tool_counts(trace)
        # 评估各路径匹配情况
        path_status = self._evaluate_node_bound_paths(task_json, successful_counts)
        matched_paths = path_status["matched_paths"]
        ground_truth = self._build_node_bound_ground_truth(task_json)

        # 定位首个被调用的扰动候选工具作为 victim
        victim_candidates = self._get_node_bound_perturbed_tools(task_json)
        victim_tool = self._find_first_alt_tool_called(trace, victim_candidates)
        if not victim_tool:
            return {
                "pass": False,
                "failure_reason": f"{mode} failed: no perturbed {complexity_label} entry tool was called",
                "trace_check": {
                    "match": False,
                    "victim_tool": None,
                    "matched_paths": matched_paths,
                    "missing_tools": path_status["closest_missing_tools"],
                    "insufficient_calls": path_status["closest_insufficient_calls"],
                    "ground_truth": ground_truth,
                    "actual": {"execution_trace": actual_trace}
                }
            }

        # 计算成功切换到不包含 victim 的其他路径
        source_paths = self._find_paths_containing_tool(task_json, victim_tool)
        switched_paths = [path_id for path_id in matched_paths if path_id not in source_paths]
        passed = len(switched_paths) > 0

        failure_reasons = []
        if not matched_paths:
            failure_reasons.append("no complete valid path executed successfully")
        if not switched_paths:
            failure_reasons.append(
                f"'{victim_tool}' failed permanently but agent did not complete another valid path"
            )

        return {
            "pass": passed,
            "failure_reason": None if passed else f"{mode} failed: {'; '.join(failure_reasons)}",
            "trace_check": {
                "match": passed,
                "victim_tool": victim_tool,
                "matched_paths": matched_paths,
                "switched_paths": switched_paths,
                "missing_tools": [] if passed else path_status["closest_missing_tools"],
                "insufficient_calls": {} if passed else path_status["closest_insufficient_calls"],
                "ground_truth": ground_truth,
                "actual": {"execution_trace": actual_trace}
            }
        }

    def _get_c3_perturbed_tools(self, task_json: Dict[str, Any]) -> Set[str]:
        """收集 C3 valid_paths 中真正被标记为 perturbation entry 的工具。"""
        return self._get_node_bound_perturbed_tools(task_json)

    def _get_node_bound_perturbed_tools(self, task_json: Dict[str, Any]) -> Set[str]:
        """收集 C3/C4 valid_paths 中真正被标记为 perturbation entry 的工具。"""
        perturbed_tools = set()
        for vp in task_json.get("valid_paths", []):
            for step in vp.get("execution_trace", []):
                if step.get("is_perturbed", False):
                    tool_name = step.get("tool_name")
                    if tool_name:
                        perturbed_tools.add(tool_name)
        return perturbed_tools

    def _find_paths_containing_tool(
        self,
        task_json: Dict[str, Any],
        tool_name: str
    ) -> Set[str]:
        """找到所有包含指定工具的 valid path。"""
        matched = set()
        for vp in task_json.get("valid_paths", []):
            tools = vp.get("tools", [])
            if tool_name in tools:
                matched.add(vp.get("path_id"))
        return matched

    def _evaluate_c3_paths(
        self,
        task_json: Dict[str, Any],
        successful_tool_counts: Counter
    ) -> Dict[str, Any]:
        """C3 路径级匹配：使用 Counter 检查完整路径是否真正完成。

        这样可以正确处理同一条路径内重复出现的工具。
        """
        return self._evaluate_node_bound_paths(task_json, successful_tool_counts)

    def _evaluate_node_bound_paths(
        self,
        task_json: Dict[str, Any],
        successful_tool_counts: Counter
    ) -> Dict[str, Any]:
        """C3/C4 路径级匹配：使用 Counter 检查完整路径是否真正完成。"""
        valid_paths = task_json.get("valid_paths", [])
        if not valid_paths:
            return {
                "matched_paths": [],
                "closest_missing_tools": [],
                "closest_insufficient_calls": {},
            }

        matched_paths: List[str] = []
        closest_missing_tools: List[str] = []
        closest_insufficient_calls: Dict[str, Dict[str, int]] = {}
        closest_score: Optional[tuple] = None

        for vp in valid_paths:
            required_tools = vp.get("tools", [])
            required_counts = Counter(required_tools)
            insufficient_calls = {}

            # 检查每种工具的调用次数是否达标
            for tool, expected_count in required_counts.items():
                actual_count = successful_tool_counts.get(tool, 0)
                if actual_count < expected_count:
                    insufficient_calls[tool] = {
                        "expected": expected_count,
                        "actual": actual_count
                    }

            # 无不足则该路径匹配成功
            if not insufficient_calls:
                matched_paths.append(vp.get("path_id"))

            # 计算缺口分数，用于选择最接近的未匹配路径
            deficit = sum(
                info["expected"] - info["actual"]
                for info in insufficient_calls.values()
            )
            score = (deficit, len(required_tools))
            if closest_score is None or score < closest_score:
                closest_score = score
                closest_missing_tools = sorted(insufficient_calls.keys())
                closest_insufficient_calls = insufficient_calls

        return {
            "matched_paths": matched_paths,
            "closest_missing_tools": closest_missing_tools,
            "closest_insufficient_calls": closest_insufficient_calls,
        }

    def _build_node_bound_ground_truth(self, task_json: Dict[str, Any]) -> Dict[str, Any]:
        """构建 C3/C4 的 ground truth 展示结构。"""
        ground_truth = self._build_c2_ground_truth(task_json)
        perturb_target = task_json.get("perturbation_target")
        if isinstance(perturb_target, dict) and perturb_target:
            ground_truth["perturbation_target"] = perturb_target
        return ground_truth

    # ========== Helper Methods ==========

    def _extract_successful_tools(self, trace: Dict[str, Any]) -> set:
        """Extract tools that were successfully executed (at least once without error).

        Args:
            trace: Execution trace

        Returns:
            Set of tool names that succeeded at least once
        """
        successful_tools = set()
        messages = self._get_messages(trace)

        # Iterate through all tool calls and their results
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("type") == "tool_call":
                call = msg.get("tool_call", {})
                tool_name = call.get("name")
                if not tool_name:
                    continue

                # Find the corresponding tool result
                call_id = call.get("id")
                result_msg = self._find_tool_result(messages, call_id, tool_name)

                if result_msg:
                    output = result_msg.get("content", {})
                    # Check if this call succeeded (no error)
                    has_error = isinstance(output, dict) and "error" in output
                    if not has_error:
                        successful_tools.add(tool_name)

        return successful_tools

    def _extract_successful_tool_counts(self, trace: Dict[str, Any]) -> Counter:
        """Extract successful tool call counts from actual execution trace."""
        successful_counts: Counter = Counter()
        messages = self._get_messages(trace)

        for msg in messages:
            if msg.get("role") != "assistant" or msg.get("type") != "tool_call":
                continue

            call = msg.get("tool_call", {})
            tool_name = call.get("name")
            if not tool_name:
                continue

            call_id = call.get("id")
            result_msg = self._find_tool_result(messages, call_id, tool_name)
            if not result_msg:
                continue

            output = result_msg.get("content", {})
            has_error = isinstance(output, dict) and "error" in output
            if not has_error:
                successful_counts[tool_name] += 1

        return successful_counts

    def _extract_ground_truth_trace(self, task_json: Dict[str, Any]) -> List[str]:
        """Extract tool names from execution_trace in task_json.

        Args:
            task_json: Task JSON data

        Returns:
            List of tool names in execution order
        """
        execution_trace = task_json.get("execution_trace", [])
        return [step["tool_name"] for step in execution_trace]

    def _find_victim_tool(self, task_json: Dict[str, Any]) -> str:
        """Find the victim tool from execution trace.

        Args:
            task_json: Task JSON data

        Returns:
            Name of the victim tool
        """
        execution_trace = task_json.get("execution_trace", [])
        for step in execution_trace:
            if step.get("is_perturbed", False):
                return step.get("tool_name", "")
        return ""

    def _load_template(self, task_json: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从 template_dir 加载对应的模板 JSON"""
        if not self.template_dir:
            return None
        template_id = task_json.get("template_id", "")
        complexity = task_json.get("complexity", "").lower()
        if not template_id or not complexity:
            return None
        path = Path(self.template_dir) / complexity / f"{template_id}.json"
        if not path.exists():
            return None
        with open(path, "r") as f:
            return json.load(f)

    # Keyword list for detecting graceful abort in final_answer.
    # Matched case-insensitively.  Add more phrases here if needed.
    _ABORT_KEYWORDS: List[str] = [
        "task abort",
        "task aborted",
        "unable to complete",
        "cannot complete",
        "could not complete",
        "failed to complete",
        "i cannot proceed",
        "i am unable to proceed",
        "terminating the task",
        "stopping the task",
    ]

    def _extract_final_answer_text(self, trace: Dict[str, Any]) -> str:
        """Return the concatenated text content of all final_answer messages."""
        parts = []
        for msg in self._get_messages(trace):
            if msg.get("type") == "final_answer":
                content = msg.get("content", "")
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, dict):
                    parts.append(json.dumps(content, ensure_ascii=False))
        return " ".join(parts)

    def _final_answer_has_abort(self, trace: Dict[str, Any]) -> bool:
        """Return True if the final_answer text contains at least one abort keyword."""
        text = self._extract_final_answer_text(trace).lower()
        return any(kw in text for kw in self._ABORT_KEYWORDS)

    def _check_p2_p4_stop_after_victim(
        self,
        task_json: Dict[str, Any],
        actual_trace: List[str],
        victim_tool: str,
        trace: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """P2/P4 通用检查：victim 出现后只允许 retry victim 本身，不得调用其他工具。

        Pass 条件：
        1. victim 之前的所有工具都被成功调用
        2. victim 工具被调用
        3. victim 首次出现之后，agent 只允许再次调用 victim 本身（retry），
           禁止调用任何其他工具
        4. 若 victim 是 execution_trace 的最后一个节点（无后置工具），
           则要求 final_answer 中包含明确的 task-abort 声明，
           否则视为模型未感知错误、直接收尾，判 fail。
        """
        execution_trace = task_json.get("execution_trace", [])

        # 定位 victim 在 execution_trace 中的索引
        victim_index = None
        for i, step in enumerate(execution_trace):
            if step.get("is_perturbed", False):
                victim_index = i
                break

        if victim_index is None:
            return {
                "match": False,
                "victim_tool": victim_tool,
                "missing_tools": [victim_tool],
                "forbidden_tools_called": [],
                "ground_truth": {"execution_trace": [s["tool_name"] for s in execution_trace]},
                "actual": {"execution_trace": actual_trace},
                "reasoning": "Victim tool not found in execution_trace"
            }

        # 必须成功调用的工具：victim 之前的非扰动工具 + victim 本身
        tools_before_victim = [
            step["tool_name"]
            for i, step in enumerate(execution_trace)
            if i < victim_index and not step.get("is_perturbed", False)
        ]
        required_tools = set(tools_before_victim) | {victim_tool}

        # 在实际轨迹中定位 victim 首次出现的位置
        victim_first_pos = None
        for i, tool in enumerate(actual_trace):
            if tool == victim_tool:
                victim_first_pos = i
                break

        if victim_first_pos is None:
            # victim 从未被调用
            missing_required = list(required_tools - set(actual_trace))
            return {
                "match": False,
                "victim_tool": victim_tool,
                "missing_tools": missing_required,
                "forbidden_tools_called": [],
                "ground_truth": {"execution_trace": [s["tool_name"] for s in execution_trace]},
                "actual": {"execution_trace": actual_trace},
                "reasoning": "Victim tool was never called"
            }

        # victim 首次出现之后调用的非 victim 工具即为违规工具
        tools_after_victim_first = actual_trace[victim_first_pos + 1:]
        forbidden_called = sorted(set(
            t for t in tools_after_victim_first if t != victim_tool
        ))

        missing_required = [t for t in required_tools if t not in set(actual_trace)]
        match = len(missing_required) == 0 and len(forbidden_called) == 0

        # ── 特殊处理：victim 为最后一个节点 ──────────────────────────────
        # 若 ground-truth 中 victim 之后无其他工具，则 forbidden_called 始终为空，
        # 无法区分 graceful abort 与静默通过。此时要求 final_answer 显式声明 abort。
        victim_is_last = not any(
            i > victim_index
            for i, step in enumerate(execution_trace)
            if not step.get("is_perturbed", False)
        )
        abort_required = victim_is_last
        abort_present = trace is not None and self._final_answer_has_abort(trace)

        if match and abort_required and not abort_present:
            match = False
            reasoning = (
                f"Victim '{victim_tool}' is the last node in the execution trace. "
                "No post-victim tool calls can distinguish graceful abort from silent pass-through. "
                "final_answer must contain an explicit abort signal, but none was found."
            )
        else:
            reasoning = (
                "After first victim call, only victim retries are allowed. "
                f"Forbidden (non-victim tools called after victim): {forbidden_called}"
            )
            if abort_required:
                reasoning += f" | victim is last node; abort_in_final_answer={abort_present}"

        return {
            "match": match,
            "victim_tool": victim_tool,
            "missing_tools": missing_required,
            "forbidden_tools_called": forbidden_called,
            "victim_is_last_node": victim_is_last,
            "abort_required": abort_required,
            "abort_in_final_answer": abort_present if abort_required else None,
            "ground_truth": {"execution_trace": [s["tool_name"] for s in execution_trace]},
            "actual": {"execution_trace": actual_trace},
            "reasoning": reasoning,
        }

    def _compute_dependent_tools(
        self, template: Dict[str, Any], victim_index: int
    ) -> Set[str]:
        """基于 parameter_bindings 计算传递依赖 victim 输出的工具集合。

        只用数据流依赖（{{sX.field}} 引用），不用 DAG edges。
        edges 在 C1 模板中表示执行顺序偏好而非真正的数据依赖。
        """
        nodes = template.get("dag", {}).get("nodes", [])
        bindings = template.get("parameter_bindings", {})
        if victim_index >= len(nodes):
            return set()

        victim_node_id = nodes[victim_index]["id"]
        id_to_tool = {n["id"]: n["tool_name"] for n in nodes}
        tool_to_id = {n["tool_name"]: n["id"] for n in nodes}

        # 解析每个工具参数中的数据引用，构建节点依赖图
        node_deps: Dict[str, Set[str]] = {n["id"]: set() for n in nodes}
        for tool_name, params in bindings.items():
            nid = tool_to_id.get(tool_name)
            if not nid:
                continue
            for value in params.values():
                if isinstance(value, list):
                    str_values = [v for v in value if isinstance(v, str)]
                else:
                    str_values = [value] if isinstance(value, str) else []
                for sv in str_values:
                    # 匹配 {{ s3.field }} 或 {{ s3 }} 形式
                    for m in re.finditer(r'\{\{\s*(s\d+)(?:\.\w+)?\s*\}\}', sv):
                        node_deps[nid].add(m.group(1))
                    # 匹配裸引用: s3.field 或 s3
                    if re.match(r'^s\d+(\.\w+)?$', sv):
                        node_deps[nid].add(sv.split(".")[0])

        # BFS 计算传递闭包，收集所有依赖 victim 的节点
        dependent_node_ids = {victim_node_id}
        changed = True
        while changed:
            changed = False
            for nid, deps in node_deps.items():
                if nid not in dependent_node_ids and deps & dependent_node_ids:
                    dependent_node_ids.add(nid)
                    changed = True

        # 将依赖节点转换为工具名（排除 victim 自身）
        dependent_tools = set()
        for nid in dependent_node_ids:
            if nid != victim_node_id and nid in id_to_tool:
                dependent_tools.add(id_to_tool[nid])
        return dependent_tools

    def _check_p2_p4_trace_dependency_aware(
        self,
        task_json: Dict[str, Any],
        actual_trace: List[str],
        victim_tool: str
    ) -> Dict[str, Any]:
        """依赖感知的 P2/P4 Trace 检查

        基于 template DAG 的 parameter_bindings 做真正的依赖分析：
        1. 必须调用：victim + victim 之前的所有工具
        2. 禁止调用：只有传递依赖 victim 输出的下游工具
        3. 不依赖 victim 的后续工具允许调用
        """
        execution_trace = task_json.get("execution_trace", [])

        # 定位 victim 在 execution_trace 中的索引
        victim_index = None
        for i, step in enumerate(execution_trace):
            if step.get("is_perturbed", False):
                victim_index = i
                break

        if victim_index is None:
            return {
                "match": False,
                "victim_tool": victim_tool,
                "missing_tools": [victim_tool],
                "ground_truth": {
                    "execution_trace": [s["tool_name"] for s in execution_trace]
                },
                "actual": {"execution_trace": actual_trace},
                "reasoning": "Victim tool not found in execution_trace"
            }

        # 将工具按 victim 位置分为前后两类
        tools_before_victim = []
        tools_after_victim = []
        for i, step in enumerate(execution_trace):
            if step.get("is_perturbed", False):
                continue
            if i < victim_index:
                tools_before_victim.append(step["tool_name"])
            elif i > victim_index:
                tools_after_victim.append(step["tool_name"])

        # 基于 DAG 计算真正依赖 victim 输出的工具集合
        template = self._load_template(task_json)
        if template:
            dependent_tools = self._compute_dependent_tools(template, victim_index)
            forbidden_tools = [t for t in tools_after_victim if t in dependent_tools]
        else:
            # 无模板时回退：所有后续工具均视为 forbidden
            forbidden_tools = tools_after_victim

        agent_tools = set(actual_trace)
        required_tools = set(tools_before_victim) | {victim_tool}
        missing_required = [t for t in required_tools if t not in agent_tools]
        forbidden_called = [t for t in forbidden_tools if t in agent_tools]

        match = len(missing_required) == 0 and len(forbidden_called) == 0

        return {
            "match": match,
            "victim_tool": victim_tool,
            "missing_tools": missing_required,
            "forbidden_tools_called": forbidden_called,
            "ground_truth": {
                "execution_trace": [s["tool_name"] for s in execution_trace]
            },
            "actual": {"execution_trace": actual_trace},
            "reasoning": f"Forbidden (depend on victim): {forbidden_tools}; independent tools are allowed"
        }

    def _extract_actual_trace(self, trace: Dict[str, Any]) -> List[str]:
        """Extract tool names from actual execution trace.

        Args:
            trace: Execution trace

        Returns:
            List of tool names in call order
        """
        messages = self._get_messages(trace)
        tool_names = []
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("type") == "tool_call":
                tool_name = msg.get("tool_call", {}).get("name")
                if tool_name:
                    tool_names.append(tool_name)
        return tool_names

    def _has_standard_sequence(self, trace: Dict[str, Any], task_json: Dict[str, Any]) -> bool:
        """Check if trace follows standard sequence."""
        # Simplified: check if no errors occurred
        return self._has_no_errors(trace)

    def _has_no_errors(self, trace: Dict[str, Any]) -> bool:
        """Check if trace has no errors."""
        for tool_result in self._iter_tool_results(trace):
            output = tool_result.get("content", {})
            if isinstance(output, dict) and "error" in output:
                return False
        return True

    def _get_error_details(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get details of all errors in trace."""
        errors = []
        for tool_result in self._iter_tool_results(trace):
            output = tool_result.get("content", {})
            if isinstance(output, dict) and "error" in output:
                errors.append({
                    "tool": tool_result.get("name", "unknown"),
                    "error": output.get("error", "unknown error")
                })
        return errors

    def _check_retry(self, trace: Dict[str, Any], victim_tool: str) -> Dict[str, Any]:
        """Check if tool was retried."""
        call_count = 0
        final_success = False
        call_details = []

        messages = self._get_messages(trace)
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("type") == "tool_call":
                call = msg.get("tool_call", {})
                if call.get("name") != victim_tool:
                    continue
                call_count += 1
                result_msg = self._find_tool_result(messages, call.get("id"), victim_tool)
                output = result_msg.get("content", {}) if result_msg else {}
                has_error = isinstance(output, dict) and "error" in output
                if not has_error:
                    final_success = True
                call_details.append({
                    "call_index": call_count,
                    "has_error": has_error,
                    "error": output.get("error") if has_error else None
                })

        return {
            "has_retry": call_count >= 2,
            "call_count": call_count,
            "final_success": final_success,
            "call_details": call_details
        }

    # ========== Message Helpers ==========

    def _get_messages(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return normalized message list."""
        return trace.get("messages", [])

    def _iter_tool_results(self, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Yield tool result messages."""
        return [
            msg for msg in self._get_messages(trace)
            if msg.get("role") == "tool"
        ]

    def _find_tool_result(
        self,
        messages: List[Dict[str, Any]],
        call_id: Optional[str],
        tool_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find the tool result message matching a call id or tool name."""
        for msg in messages:
            if msg.get("role") != "tool":
                continue
            if call_id and msg.get("call_id") == call_id:
                return msg
            if not call_id and msg.get("name") == tool_name:
                return msg
        return None
