"""Execution Engine (Sandbox) for running agents in controlled environment.

The Sandbox intercepts tool calls and injects perturbations according to
the perturbation information in the task JSON.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Ensure ToolMaze project root is on sys.path so plugins that do
# `from tools.plugins import ...` resolve correctly when sandbox is imported
# directly (without going through scripts/run_eval.py).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from toolmaze.core import ExecutionContext, ToolExecutor
from tools.loader import ToolLoader
from evaluation.agents import BaseAgent
from evaluation.utils import TraceLogger


class InferenceContext:
    """推理阶段的上下文包装器，屏蔽 user_input 和 context.data 的参数泄漏。

    插件只能使用模型传入的 arguments，不能从 context 中补全参数。
    但保留 history 的状态管理功能（如库存追踪、设备状态）。
    """

    def __init__(self):
        # 内部使用标准 ExecutionContext，但屏蔽 user_input 读取
        self._inner = ExecutionContext(user_input={})

    @property
    def user_input(self):
        # 始终返回空字典，防止参数泄漏
        return {}

    def get(self, key, default=None):
        # 禁止通过 get 访问上下文数据
        return default

    @property
    def history(self):
        # 保留历史记录访问（用于库存、状态追踪）
        return self._inner.history

    def record(self, step, tool, args, output, status, error_message=None, is_perturbed=False):
        # 委托给内部上下文记录
        self._inner.record(
            step,
            tool,
            args,
            output,
            status,
            error_message,
            is_perturbed=is_perturbed
        )

    def find_tool_output(
        self,
        tool_name,
        args_match=None,
        include_error=False,
        include_perturbed=False
    ):
        # 委托查找工具输出
        return self._inner.find_tool_output(
            tool_name,
            args_match,
            include_error=include_error,
            include_perturbed=include_perturbed
        )

    def find_alternative_output(
        self,
        tool_names,
        args_match=None,
        include_error=False,
        include_perturbed=False
    ):
        # 委托查找替代工具输出
        return self._inner.find_alternative_output(
            tool_names,
            args_match,
            include_error=include_error,
            include_perturbed=include_perturbed
        )

    def get_step_output(self, step):
        return self._inner.get_step_output(step)

    def get_from_step(self, step, key, default=None):
        return self._inner.get_from_step(step, key, default)

    def get_last_output(self):
        return self._inner.get_last_output()

    def to_trace(self):
        return self._inner.to_trace()


class ExecutionEngine:
    """Execution engine that runs agents in controlled perturbation environment."""

    def __init__(
        self,
        task_json: Dict[str, Any],
        agent: BaseAgent,
        tools_dir: Optional[str] = None
    ):
        """Initialize execution engine.

        Args:
            task_json: Complete task specification
            agent: Agent instance to evaluate
            tools_dir: Directory containing tool plugins
        """
        self.task_json = task_json
        self.agent = agent

        # 初始化 ToolLoader 与 ToolExecutor
        if tools_dir is None:
            tools_dir = str(Path(__file__).resolve().parent.parent.parent / "tools")

        plugins_dir = str(Path(tools_dir) / "plugins")
        definitions_dir = str(Path(tools_dir) / "definitions")

        self.tool_loader = ToolLoader(definitions_dir)
        self.tool_executor = ToolExecutor(
            plugins_dir=plugins_dir,
            definitions_dir=definitions_dir,
            loader=self.tool_loader
        )

        # 提取任务基本信息
        self.task_id = task_json["task_id"]
        # 优先使用 user_input["query"] 作为实际用户查询
        user_input = task_json.get("user_input", {})
        self.task_description = user_input.get("query", task_json.get("task_description", ""))
        self.mode = task_json.get("perturbation_mode", "P0")
        self.perturbation_point = task_json.get("perturbation_point", 0)
        self.complexity = task_json.get("complexity", "C1")

        # 多路径 first-touch 激活状态
        if self.complexity in ("C2", "C3", "C4"):
            self.alternative_tools = self._get_c2_alt_tools(task_json)
        else:
            self.alternative_tools = set(task_json.get("alternative_tools", []))
        self._c2_activated = False  # 是否已触发 first-touch
        self._c2_activated_tool = None  # 首次触发的 alt 工具

        # 获取执行轨迹以提取工具定义与扰动信息
        if self.complexity in ("C2", "C3", "C4"):
            self.execution_trace = self._get_c2_merged_trace(task_json)
        else:
            self.execution_trace = task_json.get("execution_trace", [])

        # C2/C3：按路径构建独立扰动映射，实现单点 first-touch 激活
        if self.complexity in ("C2", "C3"):
            self._c2_path_perturbation_maps = self._build_c2_path_maps(task_json)
            self._multi_path_activation_tools = set(self._c2_path_perturbation_maps.keys())
        else:
            self._c2_path_perturbation_maps = {}
            self._multi_path_activation_tools = set()

        # C4：按 slot 的 first-touch 状态
        # 所有扰动数据预先缓存；perturbation_map 初始为空，仅在首次调用各 slot 工具时惰性填充
        if self.complexity == "C4":
            self._c4_all_perturbed_data = self._collect_c4_perturbed_data(task_json)
            self._c4_slots, self._c4_tool_to_slot = self._build_c4_slot_map(task_json)
            self._c4_resolved_slots: set = set()
        else:
            self._c4_all_perturbed_data = {}
            self._c4_slots = {}
            self._c4_tool_to_slot = {}
            self._c4_resolved_slots = set()

        # 使用 InferenceContext 防止参数泄漏
        self.context = InferenceContext()

        # 从执行轨迹构建工具定义
        self.tool_definitions = self._build_tool_definitions()

        # 构建扰动映射：
        # - C4/C2/C3：初始为空，按 slot/path 在 first-touch 时填充
        # - C1：直接从单条 execution_trace 构建
        if self.complexity in ("C4", "C2", "C3"):
            self.perturbation_map = {}
        else:
            self.perturbation_map = self._build_perturbation_map()

        # 初始化轨迹日志
        self.logger = TraceLogger(self.task_id, self.mode)

    def _get_c2_alt_tools(self, task_json: Dict[str, Any]) -> set:
        """获取 C2 的替代工具集合。

        优先从 valid_paths 推导（并集减交集），避免历史数据里
        alternative_tools 受路径索引错位影响。
        """
        # 从 valid_paths 推断替代工具集合
        inferred = self._infer_c2_alt_tools_from_paths(task_json.get("valid_paths", []))
        if inferred:
            return inferred
        # 回退到任务中显式声明的 alternative_tools
        return set(task_json.get("alternative_tools", []))

    def _infer_c2_alt_tools_from_paths(self, valid_paths: List[Dict[str, Any]]) -> set:
        """从 valid_paths 推导替代工具：union(paths) - intersection(paths)。"""
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

    def _build_tool_definitions(self) -> List[Dict[str, Any]]:
        """Build tool definitions from execution trace.

        Returns:
            List of tool definitions
        """
        # 提取执行轨迹中所有唯一工具名
        tool_names = set()
        for step in self.execution_trace:
            tool_name = step.get("tool_name")
            if tool_name:
                tool_names.add(tool_name)

        # 从 loader 加载工具定义
        tool_definitions = []
        for tool_name in tool_names:
            tool_def = self.tool_loader.get_tool_by_name(tool_name)
            if tool_def:
                tool_definitions.append(tool_def)

        return tool_definitions

    def _build_perturbation_map(self) -> Dict[str, Dict[str, Any]]:
        """Build perturbation map from execution trace (new logic).

        Reads is_perturbed flags directly from execution_trace and stores
        the ground truth output for injection.

        Returns:
            Dictionary mapping tool_name -> {step, output, status}
        """
        perturbation_map = {}

        # 遍历 execution_trace 收集被扰动步骤
        for step_record in self.execution_trace:
            if step_record.get("is_perturbed", False):
                tool_name = step_record.get("tool_name")
                if tool_name:
                    perturbation_map[tool_name] = {
                        "step": step_record.get("step"),
                        "output": step_record.get("output", {}),
                        "status": step_record.get("status", "error")
                    }

        return perturbation_map

    def _get_c2_merged_trace(self, task_json: Dict[str, Any]) -> List[Dict]:
        """C2: 合并所有路径的工具信息，用于构建 tool_definitions。"""
        all_steps = []
        seen_tools = set()
        for vp in task_json.get("valid_paths", []):
            for step in vp.get("execution_trace", []):
                tool_name = step.get("tool_name")
                if tool_name and tool_name not in seen_tools:
                    seen_tools.add(tool_name)
                    all_steps.append(step)
        return all_steps

    def _build_c2_path_maps(self, task_json: Dict[str, Any]) -> Dict[str, Dict]:
        """C2: 为每条路径构建独立的 perturbation_map。

        Returns:
            {alt_tool_name: {tool_name: {output, status}}} 按该路径的 alt 工具名索引
        """
        path_maps = {}
        for vp in task_json.get("valid_paths", []):
            # 定位该路径中被扰动的 alt 工具
            perturb_info = {}
            alt_tool_name = None
            for step in vp.get("execution_trace", []):
                if step.get("is_perturbed", False):
                    tool_name = step.get("tool_name", "")
                    if tool_name in self.alternative_tools:
                        alt_tool_name = tool_name
                    perturb_info[tool_name] = {
                        "output": step.get("output", {}),
                        "status": step.get("status", "error")
                    }
            if alt_tool_name:
                path_maps[alt_tool_name] = perturb_info
        return path_maps

    def _collect_c4_perturbed_data(self, task_json: Dict[str, Any]) -> Dict[str, Dict]:
        """C4: 收集所有路径中标记为 is_perturbed 的步骤，作为潜在 victim 数据缓存。

        Returns:
            {tool_name: {output, status}}
        """
        data = {}
        for vp in task_json.get("valid_paths", []):
            for step in vp.get("execution_trace", []):
                if step.get("is_perturbed", False):
                    tool_name = step.get("tool_name")
                    if tool_name and tool_name not in data:
                        data[tool_name] = {
                            "output": step.get("output", {}),
                            "status": step.get("status", "error")
                        }
        return data

    def _build_c4_slot_map(self, task_json: Dict[str, Any]):
        """C4: 从 group_choices 构建 slot→工具集合 和 工具→slot_id 的映射。

        group_choices 格式：["slot_id:choice_name", ...]
        每个 slot_id 代表一个独立的 alt 分支组。同一 slot 内的工具互斥（不会同时出现在同一路径）。

        Returns:
            (slot_to_tools: {slot_id: set(tool_name)},
             tool_to_slot: {tool_name: slot_id})
        """
        alt_tools = self.alternative_tools
        paths = task_json.get("valid_paths", [])

        # 解析每条路径的 slot 选择：{path_id: {slot_id: choice}}
        path_slot_choices: Dict[str, Dict[str, str]] = {}
        for vp in paths:
            pid = vp["path_id"]
            path_slot_choices[pid] = {}
            for choice_str in vp.get("group_choices", []):
                if ":" in choice_str:
                    slot_id, choice = choice_str.split(":", 1)
                    path_slot_choices[pid][slot_id] = choice

        all_slot_ids = set()
        for choices in path_slot_choices.values():
            all_slot_ids.update(choices.keys())

        path_by_id = {vp["path_id"]: vp for vp in paths}
        slot_to_tools: Dict[str, set] = {}
        tool_to_slot: Dict[str, str] = {}

        for slot_id in all_slot_ids:
            # 按 slot 的 choice 分组路径
            choice_to_pids: Dict[str, List[str]] = {}
            for pid, choices in path_slot_choices.items():
                choice = choices.get(slot_id)
                if choice:
                    choice_to_pids.setdefault(choice, []).append(pid)

            # 每种 choice 对应的 alt 工具 = 该 choice 下所有路径的公共 alt 工具
            choice_common: Dict[str, set] = {}
            for choice, pids in choice_to_pids.items():
                tool_sets = [
                    set(path_by_id[pid].get("tools", [])) & alt_tools
                    for pid in pids if pid in path_by_id
                ]
                if tool_sets:
                    choice_common[choice] = set.intersection(*tool_sets)

            # slot 工具 = 各 choice 公共工具的并集 - 全 choice 共有工具（后者不属于本 slot）
            if choice_common:
                all_vals = list(choice_common.values())
                union_tools = set().union(*all_vals)
                common_to_all = set.intersection(*all_vals)
                slot_tools = union_tools - common_to_all
            else:
                slot_tools = set()

            slot_to_tools[slot_id] = slot_tools
            for t in slot_tools:
                if t not in tool_to_slot:
                    tool_to_slot[t] = slot_id

        return slot_to_tools, tool_to_slot

    def _activate_c2_perturbation(self, tool_name: str) -> None:
        """C2 first-touch activation: 模型首次调用某个 alt 工具时，
        激活该工具对应路径的扰动，其余 alt 工具恢复正常。"""
        if self._c2_activated or tool_name not in self._c2_path_perturbation_maps:
            return
        self._c2_activated = True
        self._c2_activated_tool = tool_name
        self.perturbation_map = self._c2_path_perturbation_maps[tool_name]

    def _activate_c4_slot_perturbation(self, tool_name: str) -> None:
        """C4 per-slot first-touch activation。

        每个 slot 内，模型第一次调用的工具成为该 slot 的 victim：
        - 将其扰动数据写入 perturbation_map（后续 _should_perturb 会持续扰动它，P2/P4）
        - 同一 slot 的其他工具不写入，保持干净（切换后不再扰动）
        - slot 标记为 resolved，后续对任何该 slot 工具的调用都不再触发激活
        """
        slot_id = self._c4_tool_to_slot.get(tool_name)
        if slot_id is None or slot_id in self._c4_resolved_slots:
            return
        self._c4_resolved_slots.add(slot_id)
        perturb_data = self._c4_all_perturbed_data.get(tool_name)
        if perturb_data:
            self.perturbation_map[tool_name] = perturb_data

    def run(self, max_rounds: int = 15) -> Tuple["TraceLogger", Dict[str, int]]:
        """Run the agent execution with perturbation interception.

        Args:
            max_rounds: Maximum number of reasoning rounds

        Returns:
            Tuple of (TraceLogger, token_usage dict)
        """
        # 初始化 Agent：设置扰动模式属性并传入任务描述与工具定义
        if hasattr(self.agent, "perturbation_mode"):
            self.agent.perturbation_mode = self.mode
        self.agent.initialize(self.task_description, self.tool_definitions)

        # 首轮使用任务描述作为用户输入
        current_message = self.task_description
        round_num = 0
        # 记录初始用户消息
        self.logger.log_user_message(self.task_description)

        while round_num < max_rounds:
            round_num += 1

            # Agent 执行一步推理
            action = self.agent.step(user_message=current_message if round_num == 1 else None)

            # 将 AgentAction 转为字典以便日志记录
            action_dict = {
                "type": action.type,
                "tool_name": action.tool_name,
                "arguments": action.arguments,
                "content": action.content,
                "thought": action.thought
            }

            # 若返回最终答案则记录并结束
            if action.type == "final_answer":
                self.logger.log_round(
                    round_num=round_num,
                    agent_action=action_dict,
                    tool_result=None,
                    perturbation_status="n/a"
                )
                break

            # 若返回 tool_call 则拦截并可能注入扰动
            if action.type == "tool_call":
                # 处理并行 tool_calls
                if action.tool_calls and len(action.tool_calls) > 1:
                    for idx, tc in enumerate(action.tool_calls):
                        tool_result, perturbation_status = self._intercept_tool_call(
                            tc.tool_name,
                            tc.arguments
                        )

                        tc_action_dict = {
                            "type": action.type,
                            "tool_name": tc.tool_name,
                            "arguments": tc.arguments,
                            "content": action.content if idx == 0 else None,
                            "thought": action.thought if idx == 0 else None
                        }

                        self.logger.log_round(
                            round_num=round_num,
                            agent_action=tc_action_dict,
                            tool_result=tool_result,
                            perturbation_status=perturbation_status
                        )

                        self.agent.receive_tool_result(tc.tool_name, tool_result, tool_call_index=idx)
                else:
                    # 单工具调用
                    tool_result, perturbation_status = self._intercept_tool_call(
                        action.tool_name,
                        action.arguments
                    )

                    self.logger.log_round(
                        round_num=round_num,
                        agent_action=action_dict,
                        tool_result=tool_result,
                        perturbation_status=perturbation_status
                    )

                    self.agent.receive_tool_result(action.tool_name, tool_result)

                # 后续轮次不再重复传入 user_message
                current_message = None

        # 汇总 token 消耗
        token_usage = self.agent.get_token_usage().to_dict()

        return self.logger, token_usage

    def _should_perturb(self, tool_name: str) -> bool:
        """Check if the current tool call should be perturbed.

        Perturbation is injected only on the first call to the tool.

        Args:
            tool_name: Name of the tool being called

        Returns:
            True if perturbation should be injected, False otherwise
        """
        if tool_name not in self.perturbation_map:
            return False

        # P2/P4: 永久扰动——每次调用都返回扰动数据
        if self.mode in ("P2", "P4"):
            return True

        # P1/P3: 瞬态扰动——仅首次调用被扰动
        call_count = sum(1 for r in self.context.history if r.tool_name == tool_name)
        return call_count == 0

    def _intercept_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """Intercept tool call and apply perturbation if needed.

        Args:
            tool_name: Name of the tool being called
            arguments: Tool arguments

        Returns:
            Tuple of (tool_result, perturbation_status)
            perturbation_status: "clean", "perturbed", or "n/a"
        """
        step = len(self.context.history) + 1

        # C2: 保持原有 first-touch activation 语义
        if self.complexity == "C2" and tool_name in self.alternative_tools:
            self._activate_c2_perturbation(tool_name)

        # C3: 仅在命中当前任务真正可扰动的 path entry tool 时激活
        if self.complexity == "C3" and tool_name in self._multi_path_activation_tools:
            self._activate_c2_perturbation(tool_name)

        # C4: 按 slot 的 first-touch activation
        if self.complexity == "C4" and tool_name in self.alternative_tools:
            self._activate_c4_slot_perturbation(tool_name)

        # 判断是否需要注入扰动
        if self._should_perturb(tool_name):
            # 使用 ground truth 数据注入扰动
            perturb_info = self.perturbation_map[tool_name]
            result = perturb_info["output"]
            status = perturb_info["status"]

            # 记录到上下文
            self.context.record(
                step,
                tool_name,
                arguments,
                result,
                status,
                is_perturbed=True
            )
            return result, "perturbed"

        # 未触发扰动，执行真实工具
        result = self.tool_executor.execute(tool_name, arguments, self.context, step)
        return result, "clean"
