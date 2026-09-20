"""OpenAI-based Agent implementation using Function Calling."""

import json
from typing import Dict, Any, Optional, List
from openai import OpenAI
import time

from .base_agent import BaseAgent, AgentAction, TokenUsage, ToolCall


class OpenAIAgent(BaseAgent):
    """Agent implementation using OpenAI Chat Completions API with Function Calling."""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize OpenAI agent.

        Args:
            model: Model name (e.g., gpt-4o, gpt-3.5-turbo)
            api_key: OpenAI API key
            base_url: Optional base URL (for VLLM compatibility)
            temperature: Sampling temperature
            max_tokens: Max tokens per response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # 状态变量
        self.messages: List[Dict[str, Any]] = []
        self.tools: List[Dict[str, Any]] = []
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.task_description: str = ""

        # 由 ExecutionEngine 在执行前设置，用于选择对应系统提示
        # None 表示扰动模式，使用 fault-aware 提示
        self.perturbation_mode: Optional[str] = None

        # 强制使用 P0 系统提示（忽略扰动模式）
        self.force_p0_prompt: bool = False

    def initialize(self, task_description: str, tool_definitions: Dict[str, Any]) -> None:
        """Initialize with task and tools."""
        self.task_description = task_description
        self.messages = []
        self.input_tokens = 0
        self.output_tokens = 0

        # 将工具定义转换为 OpenAI Function Calling 格式
        self.tools = self._convert_tool_definitions(tool_definitions)

        # 构建并添加系统消息
        system_message = self._build_system_message()
        self.messages.append({
            "role": "system",
            "content": system_message
        })

    def step(self, user_message: Optional[str] = None) -> AgentAction:
        """Execute one reasoning step."""
        # 首轮传入 user_message（通常为任务描述）
        if user_message:
            self.messages.append({
                "role": "user",
                "content": user_message
            })

        # 调用 OpenAI API，带指数退避重试
        try:
            max_retries = 5
            base_delay = 2
            
            for attempt in range(max_retries):
                # if attempt == 0:
                #     print("\n" + "="*50)
                #     print("1. MESSAGES HISTORY:")
                #     print(json.dumps(self.messages, indent=2, ensure_ascii=False))
                #     print("\n2. LAST MESSAGE LENGTH:", len(str(self.messages[-1])))
                #     print("="*50 + "\n")
                try:
                    # 发起聊天补全请求
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=self.messages,
                        tools=self.tools if self.tools else None,
                        parallel_tool_calls=False,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        timeout=45.0,
                    )
                except Exception as e:
                    # 识别可重试的瞬态错误
                    error_msg = str(e).lower()
                    last_error = str(e)
                    is_transient = (
                        "502" in error_msg or "503" in error_msg or
                        "connection" in error_msg or "timeout" in error_msg or
                        "rate limit" in error_msg or
                        ("400" in error_msg and "context_length" not in error_msg and "invalid_request" not in error_msg)
                    )
                    if is_transient:
                        if attempt < max_retries - 1:
                            sleep_time = base_delay * (2 ** attempt)
                            print(f"⚠️ Network/Server error: {error_msg}. Retrying in {sleep_time}s (Attempt {attempt+1}/{max_retries})...")
                            time.sleep(sleep_time)
                            continue
                    return AgentAction(
                        type="final_answer",
                        content=f"Error during execution: {last_error}"
                    )

                choice = response.choices[0]
                message = choice.message
                
                is_empty = False
                msg_dict = None

                # 处理不同 SDK 版本的响应格式差异
                if message is None:
                    raw_tool_calls = getattr(choice, 'tool_calls', None)
                    raw_content = getattr(choice, 'content', None)
                    raw_reasoning = getattr(choice, 'reasoning_content', None)

                    if raw_tool_calls:
                        msg_dict = {
                            "role": getattr(choice, 'role', 'assistant') or "assistant",
                            "content": raw_content or "",
                            "tool_calls": raw_tool_calls
                        }
                        if raw_reasoning:
                            msg_dict["reasoning_content"] = raw_reasoning
                    elif raw_content and str(raw_content).strip():
                        msg_dict = {
                            "role": getattr(choice, 'role', 'assistant') or "assistant",
                            "content": raw_content
                        }
                    else:
                        is_empty = True
                else:
                    msg_dict = message.model_dump(exclude_none=True)
                    if msg_dict.get("content") is None:
                        msg_dict["content"] = ""
                    # 保留 reasoning_content（兼容 Kimi 等推理模型）
                    if msg_dict.get("tool_calls") and "reasoning_content" not in msg_dict:
                        reasoning = getattr(message, 'reasoning_content', None)
                        if reasoning:
                            msg_dict["reasoning_content"] = reasoning

                    if not msg_dict.get("tool_calls") and not msg_dict.get("function_call") and not str(msg_dict.get("content", "")).strip():
                        is_empty = True

                # 限制单次只处理一个 tool_call
                if msg_dict and msg_dict.get("tool_calls") and len(msg_dict["tool_calls"]) > 1:
                    msg_dict["tool_calls"] = [msg_dict["tool_calls"][0]]

                # 空响应时重试
                if is_empty:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Model returned an empty response. Retrying (Attempt {attempt+1}/{max_retries})...")
                        continue
                    else:
                        return AgentAction(
                            type="final_answer",
                            content="Error: Model repeatedly returned empty responses without tool calls or final answer."
                        )

                # 累加 token 消耗
                if hasattr(response, 'usage') and response.usage:
                    self.input_tokens += response.usage.prompt_tokens
                    self.output_tokens += response.usage.completion_tokens
                
                if msg_dict is None:
                    msg_dict = {"role": "assistant", "content": ""}
                    
                self.messages.append(msg_dict)

                # 处理 function_call 格式（兼容旧版）
                tool_calls_list = msg_dict.get("tool_calls", [])
                if not tool_calls_list and "function_call" in msg_dict:
                    fc = msg_dict["function_call"]
                    return AgentAction(
                        type="tool_call",
                        tool_name=fc.get("name") if isinstance(fc, dict) else fc.name,
                        arguments=json.loads(fc.get("arguments", "{}") if isinstance(fc, dict) else (fc.arguments or "{}")),
                        thought=msg_dict.get("content")
                    )

                # 处理 tool_calls 格式
                if tool_calls_list:
                    first_call = tool_calls_list[0]
                    if isinstance(first_call, dict):
                        tool_name = first_call.get("function", {}).get("name")
                        arguments_str = first_call.get("function", {}).get("arguments", "{}")
                    else:
                        tool_name = first_call.function.name
                        arguments_str = first_call.function.arguments

                    return AgentAction(
                        type="tool_call",
                        tool_name=tool_name,
                        arguments=json.loads(arguments_str) if arguments_str else {},
                        thought=msg_dict.get("content")
                    )

                # 无 tool_call，返回最终文本答案
                return AgentAction(
                    type="final_answer",
                    content=msg_dict.get("content", "")
                )

        except Exception as e:
            return AgentAction(
                type="final_answer",
                content=f"Error during execution: {str(e)}"
            )

    def receive_tool_result(self, tool_name: str, result: Dict[str, Any], tool_call_index: int = 0) -> None:
        """Receive tool result and add to conversation.

        Args:
            tool_name: Name of the tool
            result: Tool execution result
            tool_call_index: Index of the tool call in parallel calls (default 0)
        """
        # 从最近一条带 tool_calls 的 assistant 消息中找到对应 call_id
        for i in range(len(self.messages) - 1, -1, -1):
            msg = self.messages[i]
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                tool_calls = msg["tool_calls"]
                if tool_call_index < len(tool_calls):
                    tool_call_id = tool_calls[tool_call_index]["id"]
                else:
                    tool_call_id = tool_calls[0]["id"]

                # 将工具结果以 tool role 追加到对话历史
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })
                break

    def get_total_tokens(self) -> int:
        """Get total tokens consumed."""
        return self.input_tokens + self.output_tokens

    def get_token_usage(self) -> TokenUsage:
        """Get detailed token usage statistics."""
        return TokenUsage(
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens
        )

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.messages.copy()

    def reset(self) -> None:
        """Reset agent state."""
        self.messages = []
        self.input_tokens = 0
        self.output_tokens = 0

    # ========== Helper Methods ==========

    def _build_system_message(self) -> str:
        """Select and build the system message based on perturbation mode."""
        if self.force_p0_prompt or self.perturbation_mode == "P0":
            return self._build_p0_system_message()
        return self._build_perturbation_system_message()

    def _build_p0_system_message(self) -> str:
        """System prompt for P0 (no perturbation): focus on complete execution."""
        return """You are an autonomous AI assistant that executes tool-based workflows.

TASK COMPLETION
- The user query may describe multiple sub-tasks. You must complete ALL of them — do NOT skip any sub-tasks.
- Every fact, data retrieval, or state change must come from a tool call. Never substitute a tool result with internal knowledge, and never report a step as completed unless you actually called the corresponding tool and received its result in this conversation.

FINAL ANSWER FORMAT
- Be CONCISE and DIRECT. No emojis, markdown formatting (**, ✅, etc.), or bullet points.
- State only essential facts and requested results (e.g., confirmation codes). Omit internal technical details."""

    def _build_perturbation_system_message(self) -> str:
        """System prompt for P1–P4 (perturbation modes): fault-aware execution."""
        return """You are an autonomous AI assistant that executes tool-based workflows. Tools may occasionally fail or return unexpected data.

TASK COMPLETION
- The user query may describe multiple sub-tasks. You must complete ALL of them — do NOT skip any sub-tasks.
- Every fact, data retrieval, or state change must come from a tool call. Never substitute a tool result with internal knowledge, and never report a step as completed unless you actually called the corresponding tool and received its result in this conversation.
- Sub-tasks may be accomplishable through different tool combinations.

FAULT HANDLING
- When evaluating tool outputs, consider whether the returned data is coherent and usable for the next step — fields should be present, values should be semantically reasonable, and types should match what the workflow requires.
- If you determine that a required step cannot be accomplished by any available tool or approach, stop the workflow and clearly report which step failed and why, rather than proceeding with incomplete results.

FINAL ANSWER FORMAT
- Be CONCISE and DIRECT. No emojis, markdown formatting (**, ✅, etc.), or bullet points.
- If SUCCESSFUL: State only essential facts and requested results (e.g., confirmation codes). Omit internal technical details.
- If HALTED: State clearly that the task was aborted and the reason (e.g., "Task aborted: the pricing tool returned corrupted data after retry and no other alternative approaches exist"). Do not apologize excessively."""

    def _convert_tool_definitions(self, tool_definitions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert tool definitions to OpenAI Function Calling format.

        Args:
            tool_definitions: Tool definitions from task JSON

        Returns:
            List of tool definitions in OpenAI format
        """
        # 若已为标准 function_call 格式则直接返回
        if "function_call" in tool_definitions:
            return tool_definitions["function_call"]

        tools = []

        # 列表格式：逐个提取 spec 或兜底转换
        if isinstance(tool_definitions, list):
            for tool_def in tool_definitions:
                if "paradigms" in tool_def and "function_call" in tool_def["paradigms"]:
                    spec = tool_def["paradigms"]["function_call"]["spec"]
                    tools.append({
                        "type": "function",
                        "function": spec
                    })
                else:
                    tool_name = tool_def.get("name", "unknown")
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": tool_def.get("description", ""),
                            "parameters": tool_def.get("parameters", {"type": "object", "properties": {}})
                        }
                    })
        else:
            # 字典格式：遍历工具名与定义
            for tool_name, tool_def in tool_definitions.items():
                if "paradigms" in tool_def and "function_call" in tool_def["paradigms"]:
                    spec = tool_def["paradigms"]["function_call"]["spec"]
                    tools.append({
                        "type": "function",
                        "function": spec
                    })
                else:
                    # 非标准格式兜底转换
                    tools.append({
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": tool_def.get("description", ""),
                            "parameters": tool_def.get("parameters", {"type": "object", "properties": {}})
                        }
                    })

        return tools
