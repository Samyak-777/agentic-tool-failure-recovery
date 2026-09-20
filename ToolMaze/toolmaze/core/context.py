"""
core/context.py - ExecutionContext 执行上下文

数据一致性的核心组件，负责工具间数据传递。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from .types import StepRecord, StepStatus


@dataclass
class ExecutionContext:
    """
    执行上下文 - 工具间数据传递的核心

    解决的问题：
    - 工具之间的数据传递
    - 保证数据一致性
    - 支持跳步引用（如 s1 的输出被 s3 使用）
    """

    history: List[StepRecord] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    user_input: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def record(
        self,
        step: int,
        tool: str,
        args: Dict[str, Any],
        output: Dict[str, Any],
        status: str = "success",
        error_message: Optional[str] = None,
        is_perturbed: bool = False
    ) -> None:
        """
        记录执行步骤，自动累积输出到 data

        Args:
            step: 步骤编号
            tool: 工具名称
            args: 工具参数
            output: 工具输出
            status: 执行状态 ("success" | "error")
            error_message: 错误信息（可选）
            is_perturbed: 是否为扰动注入结果（可选）
        """
        step_status = StepStatus(status)
        record = StepRecord(
            step=step,
            tool_name=tool,
            arguments=args,
            output=output,
            status=step_status,
            error_message=error_message,
            is_perturbed=is_perturbed
        )
        self.history.append(record)

        # 成功时累积输出到 data
        if step_status == StepStatus.SUCCESS and isinstance(output, dict):
            self.data.update(output)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取上下文数据（优先从累积数据，其次从 user_input）

        Args:
            key: 数据键名
            default: 默认值

        Returns:
            数据值或默认值
        """
        if key in self.data:
            return self.data[key]
        return self.user_input.get(key, default)

    def get_step_output(self, step: int) -> Optional[Dict[str, Any]]:
        """
        获取指定步骤的输出

        Args:
            step: 步骤编号

        Returns:
            步骤输出字典或 None
        """
        for record in self.history:
            if record.step == step:
                return record.output
        return None

    def get_from_step(self, step: int, key: str, default: Any = None) -> Any:
        """
        获取指定步骤输出中的特定字段（解决跳步引用问题）

        Args:
            step: 步骤编号
            key: 字段名
            default: 默认值

        Returns:
            字段值或默认值
        """
        output = self.get_step_output(step)
        if output and isinstance(output, dict):
            if key in output:
                return output[key]
            # fallback: "result" 是通用占位符，尝试常见输出字段
            if key == "result":
                for fallback_key in ("price", "value", "total", "data", "content"):
                    if fallback_key in output:
                        return output[fallback_key]
        return default

    def get_last_output(self) -> Optional[Dict[str, Any]]:
        """获取最后一步的输出"""
        return self.history[-1].output if self.history else None

    def get_last_step(self) -> Optional[StepRecord]:
        """获取最后一步的记录"""
        return self.history[-1] if self.history else None

    def _is_reusable_record(
        self,
        record: StepRecord,
        include_error: bool = False,
        include_perturbed: bool = False
    ) -> bool:
        """判断记录是否可被复用。"""
        if not include_perturbed and record.is_perturbed:
            return False

        # 默认不复用 error 输出；仅当显式允许时复用
        if not include_error and isinstance(record.output, dict) and "error" in record.output:
            return False

        return True

    def find_tool_output(
        self,
        tool_name: str,
        args_match: Dict[str, Any] = None,
        include_error: bool = False,
        include_perturbed: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        查找指定工具的输出（用于可替换工具的一致性检查）

        Args:
            tool_name: 工具名称
            args_match: 需要匹配的参数（可选）
            include_error: 是否允许复用错误结果（默认 False）
            include_perturbed: 是否允许复用扰动结果（默认 False）

        Returns:
            匹配的输出或 None
        """
        for record in self.history:
            if record.tool_name == tool_name:
                if not self._is_reusable_record(
                    record,
                    include_error=include_error,
                    include_perturbed=include_perturbed
                ):
                    continue
                if args_match is None:
                    return record.output
                # 检查参数是否匹配
                if all(record.arguments.get(k) == v for k, v in args_match.items()):
                    return record.output
        return None

    def find_alternative_output(
        self,
        tool_names: List[str],
        args_match: Dict[str, Any] = None,
        include_error: bool = False,
        include_perturbed: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        查找可替换工具组中任一工具的输出

        Args:
            tool_names: 可替换工具名称列表
            args_match: 需要匹配的参数
            include_error: 是否允许复用错误结果（默认 False）
            include_perturbed: 是否允许复用扰动结果（默认 False）

        Returns:
            匹配的输出或 None
        """
        for record in self.history:
            if record.tool_name in tool_names:
                if not self._is_reusable_record(
                    record,
                    include_error=include_error,
                    include_perturbed=include_perturbed
                ):
                    continue
                if args_match is None:
                    return record.output
                if all(record.arguments.get(k) == v for k, v in args_match.items()):
                    return record.output
        return None

    def to_trace(self) -> List[Dict[str, Any]]:
        """导出为 execution_trace 格式"""
        return [record.to_dict() for record in self.history]

    def clone(self) -> "ExecutionContext":
        """创建上下文的深拷贝"""
        import copy
        return ExecutionContext(
            history=[copy.deepcopy(r) for r in self.history],
            data=copy.deepcopy(self.data),
            user_input=copy.deepcopy(self.user_input),
            metadata=copy.deepcopy(self.metadata)
        )
