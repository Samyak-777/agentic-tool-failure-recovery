"""
core/executor.py - ToolExecutor 工具执行引擎

从 tools/runtime.py 拆分而来，负责工具执行并自动记录到上下文。
"""

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, List

from .context import ExecutionContext
from .types import StepStatus


class ToolExecutor:
    """
    工具执行引擎

    职责：
    - 加载工具插件
    - 执行工具并验证参数
    - 自动记录执行结果到 ExecutionContext
    """

    def __init__(
        self,
        plugins_dir: str,
        definitions_dir: str,
        loader: Optional[Any] = None
    ):
        """
        初始化工具执行器

        Args:
            plugins_dir: 插件目录路径
            definitions_dir: 工具定义目录路径
            loader: 可选的 ToolLoader 实例
        """
        self.plugins_dir = Path(plugins_dir)
        self.definitions_dir = Path(definitions_dir)
        self.plugins: Dict[str, Any] = {}
        self.loader = loader
        self._load_plugins()

    def _load_plugins(self) -> None:
        """加载所有工具插件"""
        if not self.plugins_dir.exists():
            return

        for plugin_file in self.plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    tool_name = getattr(module, "TOOL_NAME", plugin_file.stem)
                    self.plugins[tool_name] = module
            except Exception as e:
                print(f"Warning: Failed to load plugin {plugin_file}: {e}")

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: ExecutionContext,
        step: int
    ) -> Dict[str, Any]:
        """
        执行工具并记录到上下文

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            context: 执行上下文
            step: 步骤编号

        Returns:
            工具输出字典
        """
        # 0. 自动类型转换（number → string）
        arguments = self._coerce_types(tool_name, arguments)

        # 1. 参数验证
        errors = self._validate(tool_name, arguments)
        if errors:
            output = {"error": "Validation failed", "details": errors}
            context.record(step, tool_name, arguments, output, "error")
            return output

        # 2. 执行插件
        if tool_name not in self.plugins:
            output = {"error": f"Plugin not found: {tool_name}"}
            context.record(step, tool_name, arguments, output, "error")
            return output

        try:
            plugin = self.plugins[tool_name]
            output = plugin.execute(arguments, context)
        except Exception as e:
            output = {"error": str(e)}
            context.record(step, tool_name, arguments, output, "error")
            return output

        # 3. 记录到上下文
        status = "error" if "error" in output else "success"
        context.record(step, tool_name, arguments, output, status)
        return output

    def _validate(self, tool_name: str, arguments: Dict[str, Any]) -> List[str]:
        """
        验证工具参数

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []

        if not self.loader:
            return errors

        tool_def = self.loader.get_tool_by_name(tool_name)
        if not tool_def:
            return errors

        # 获取参数 schema
        params_schema = tool_def.get("paradigms", {}).get(
            "function_call", {}
        ).get("spec", {}).get("parameters", {})

        required = params_schema.get("required", [])
        properties = params_schema.get("properties", {})

        # 检查必需参数
        for param in required:
            if param not in arguments:
                errors.append(f"Missing required parameter: {param}")

        # 检查参数类型
        for param, value in arguments.items():
            if param in properties:
                expected_type = properties[param].get("type")
                if not self._check_type(value, expected_type):
                    errors.append(
                        f"Parameter '{param}' type mismatch: "
                        f"expected {expected_type}"
                    )

        return errors

    def _coerce_types(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """自动类型转换：如 number → string"""
        if not self.loader:
            return arguments
        tool_def = self.loader.get_tool_by_name(tool_name)
        if not tool_def:
            return arguments
        props = tool_def.get("paradigms", {}).get(
            "function_call", {}
        ).get("spec", {}).get("parameters", {}).get("properties", {})
        for param, value in arguments.items():
            if param in props:
                expected = props[param].get("type")
                if expected == "string" and isinstance(value, (int, float)):
                    arguments[param] = str(value)
                elif expected == "number" and isinstance(value, str):
                    try:
                        arguments[param] = float(value)
                    except ValueError:
                        pass
        return arguments

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值是否符合预期类型"""
        if expected_type is None:
            return True

        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected = type_map.get(expected_type)
        if expected is None:
            return True

        return isinstance(value, expected)

    def get_plugin(self, tool_name: str) -> Optional[Any]:
        """获取工具插件模块"""
        return self.plugins.get(tool_name)

    def has_plugin(self, tool_name: str) -> bool:
        """检查是否存在指定工具的插件"""
        return tool_name in self.plugins

    def list_tools(self) -> List[str]:
        """列出所有已加载的工具"""
        return list(self.plugins.keys())
