"""
core/types.py - 类型定义

定义数据构造系统中使用的核心类型和协议。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Protocol, TypedDict
from enum import Enum


class StepStatus(str, Enum):
    """步骤执行状态"""
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class ToolCategory(str, Enum):
    """工具类别"""
    SOURCE = "Source"
    PROCESSOR = "Processor"
    ACTION = "Action"


class PerturbationMode(str, Enum):
    """扰动模式"""
    P0_IDEAL = "P0"
    P1_EXPLICIT_TRANSIENT = "P1"
    P2_EXPLICIT_PERMANENT = "P2"
    P3_IMPLICIT_TRANSIENT = "P3"
    P4_IMPLICIT_PERMANENT = "P4"


class Complexity(str, Enum):
    """任务复杂度"""
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"


@dataclass
class StepRecord:
    """单步执行记录"""
    step: int
    tool_name: str
    arguments: Dict[str, Any]
    output: Dict[str, Any]
    status: StepStatus = StepStatus.SUCCESS
    error_message: Optional[str] = None
    is_perturbed: bool = False  # 标记该步骤是否被扰动
    is_optional: bool = False  # 标记该步骤是否为可选（用于 P2/P4）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "step": self.step,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "output": self.output,
            "status": self.status.value
        }
        if self.error_message:
            result["error_message"] = self.error_message
        if self.is_perturbed:
            result["is_perturbed"] = self.is_perturbed
        if self.is_optional:
            result["is_optional"] = self.is_optional
        return result


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    context_keys: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    category: ToolCategory
    domain: str
    parameters: List[ToolParameter]
    returns: List[Dict[str, Any]]
    substitutes: List[str] = field(default_factory=list)
    prerequisites: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AlternativePath:
    """单条替代路径"""
    path_id: str
    tools: List[Dict[str, Any]]


@dataclass
class AlternativeGroup:
    """一组可替换的路径"""
    alt_id: str
    description: str
    domain: str
    paths: List[AlternativePath]
    alt_type: str  # e.g. "one_to_one", "one_to_many", "many_to_many"
    output_schema: Optional[Dict[str, Any]] = None


class ToolExecutorProtocol(Protocol):
    """工具执行器协议"""

    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: "ExecutionContextProtocol",
        step: int
    ) -> Dict[str, Any]:
        """执行工具"""
        ...


class ExecutionContextProtocol(Protocol):
    """执行上下文协议"""

    def record(
        self,
        step: int,
        tool: str,
        args: Dict[str, Any],
        output: Dict[str, Any],
        status: str,
        error_message: Optional[str] = None,
        is_perturbed: bool = False
    ) -> None:
        """记录执行步骤"""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        ...

    def get_step_output(self, step: int) -> Optional[Dict[str, Any]]:
        """获取指定步骤的输出"""
        ...


class TemplateStrategyProtocol(Protocol):
    """模板策略协议"""

    complexity: str

    def validate_chain(self, chain: List[Dict]) -> List[str]:
        """验证工具链"""
        ...

    def build_dag(self, chain: List[Dict]) -> Dict:
        """构建 DAG"""
        ...

    def serialize(self, dag: Dict, metadata: Dict) -> Dict:
        """序列化为模板格式"""
        ...


class PerturbationModeProtocol(Protocol):
    """扰动模式协议"""

    name: str
    mode_type: str  # "explicit" | "implicit"
    duration: str   # "transient" | "permanent"

    def apply(
        self,
        trace: List[StepRecord],
        point: int,
        llm_client: Any = None
    ) -> List[StepRecord]:
        """应用扰动"""
        ...


class ValidatorProtocol(Protocol):
    """验证器协议"""

    def validate(self, task: Dict[str, Any]) -> "ValidationResult":
        """验证任务"""
        ...


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    issues: List[Dict[str, Any]] = field(default_factory=list)

    def add_issue(
        self,
        issue_type: str,
        message: str,
        **kwargs
    ) -> None:
        """添加问题"""
        issue = {
            "type": issue_type,
            "message": message,
            **kwargs
        }
        self.issues.append(issue)
        self.valid = False


# TypedDict 定义用于更精确的类型提示
class TaskDict(TypedDict, total=False):
    """任务字典类型"""
    task_id: str
    template_id: str
    complexity: str
    task_description: str
    user_input: Dict[str, Any]
    execution_trace: List[Dict[str, Any]]
    expected_result: Dict[str, Any]
    domains: List[str]


class TemplateDict(TypedDict, total=False):
    """模板字典类型"""
    template_id: str
    complexity: str
    task_goal: str
    domains: List[str]
    dag: Dict[str, Any]
    parameter_bindings: Dict[str, Any]
