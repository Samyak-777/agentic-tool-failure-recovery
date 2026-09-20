"""Anthropic Claude-based Agent implementation."""

import json
from typing import Dict, Any, Optional, List
from anthropic import Anthropic

from .base_agent import BaseAgent, AgentAction, TokenUsage, ToolCall


class AnthropicAgent(BaseAgent):
    """Agent implementation using Anthropic Claude API with Tool Use."""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize Anthropic agent.

        Args:
            model: Model name (e.g., claude-3-5-sonnet-20241022)
            api_key: Anthropic API key
            temperature: Sampling temperature
            max_tokens: Max tokens per response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize Anthropic client
        self.client = Anthropic(api_key=api_key)

        # State
        self.messages: List[Dict[str, Any]] = []
        self.tools: List[Dict[str, Any]] = []
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.system_message: str = ""

    def initialize(self, task_description: str, tool_definitions: Dict[str, Any]) -> None:
        """Initialize with task and tools."""
        self.messages = []
        self.input_tokens = 0
        self.output_tokens = 0

        # Convert tool definitions to Anthropic Tool Use format
        self.tools = self._convert_tool_definitions(tool_definitions)

        # Build system message
        self.system_message = self._build_system_message()

    def step(self, user_message: Optional[str] = None) -> AgentAction:
        """Execute one reasoning step."""
        # Add user message if provided
        if user_message:
            self.messages.append({
                "role": "user",
                "content": user_message
            })

        # Call Anthropic API
        try:
            response = self.client.messages.create(
                model=self.model,
                system=self.system_message,
                messages=self.messages,
                tools=self.tools if self.tools else None,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Update token count
            if hasattr(response, 'usage'):
                self.input_tokens += response.usage.input_tokens
                self.output_tokens += response.usage.output_tokens

            # Parse response
            content_blocks = response.content

            # Build assistant message
            assistant_message = {
                "role": "assistant",
                "content": content_blocks
            }
            self.messages.append(assistant_message)

            # Check for tool use
            tool_use_blocks = [b for b in content_blocks if b.type == "tool_use"]

            if tool_use_blocks:
                # Extract thought (text before tool use)
                thought = None
                for b in content_blocks:
                    if b.type == "text":
                        thought = b.text
                        break

                if len(tool_use_blocks) == 1:
                    # Single tool call
                    block = tool_use_blocks[0]
                    return AgentAction(
                        type="tool_call",
                        tool_name=block.name,
                        arguments=block.input,
                        thought=thought
                    )
                else:
                    # Multiple parallel tool calls
                    calls = [
                        ToolCall(tool_name=b.name, arguments=b.input)
                        for b in tool_use_blocks
                    ]
                    return AgentAction(
                        type="tool_call",
                        tool_name=calls[0].tool_name,
                        arguments=calls[0].arguments,
                        thought=thought,
                        tool_calls=calls
                    )

            # Otherwise, extract text as final answer
            final_text = ""
            for block in content_blocks:
                if block.type == "text":
                    final_text += block.text

            return AgentAction(
                type="final_answer",
                content=final_text
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
        # Find the last assistant message with tool_use blocks
        for i in range(len(self.messages) - 1, -1, -1):
            msg = self.messages[i]
            if msg.get("role") == "assistant":
                tool_use_blocks = [
                    b for b in msg.get("content", [])
                    if hasattr(b, 'type') and b.type == "tool_use"
                ]
                if not tool_use_blocks:
                    continue

                if tool_call_index < len(tool_use_blocks):
                    tool_use_id = tool_use_blocks[tool_call_index].id
                else:
                    tool_use_id = tool_use_blocks[0].id

                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result, ensure_ascii=False)
                }

                # Append to existing user message if last message is already a tool_result user message
                if (self.messages and
                    self.messages[-1].get("role") == "user" and
                    isinstance(self.messages[-1].get("content"), list) and
                    self.messages[-1]["content"] and
                    isinstance(self.messages[-1]["content"][0], dict) and
                    self.messages[-1]["content"][0].get("type") == "tool_result"):
                    self.messages[-1]["content"].append(tool_result_block)
                else:
                    self.messages.append({
                        "role": "user",
                        "content": [tool_result_block]
                    })
                return

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
        """Build system message for the agent."""
        return """You are a helpful AI assistant that can use tools to solve tasks.

When using tools:
1. Think step by step about what information you need
2. Call tools one at a time and wait for results
3. If a tool fails, consider retrying or using alternative approaches
4. If a tool returns unexpected data, verify it makes sense before using it
5. When you have completed the task, provide a clear final answer

Always provide clear explanations of your reasoning and actions."""

    def _convert_tool_definitions(self, tool_definitions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert tool definitions to Anthropic Tool Use format.

        Args:
            tool_definitions: Tool definitions from task JSON

        Returns:
            List of tool definitions in Anthropic format
        """
        tools = []

        # Handle list format (from _build_tool_definitions)
        if isinstance(tool_definitions, list):
            for tool_def in tool_definitions:
                if "paradigms" in tool_def and "function_call" in tool_def["paradigms"]:
                    spec = tool_def["paradigms"]["function_call"]["spec"]
                    tools.append({
                        "name": spec.get("name", tool_def.get("name", "unknown")),
                        "description": spec.get("description", ""),
                        "input_schema": spec.get("parameters", {"type": "object", "properties": {}})
                    })
                else:
                    tools.append({
                        "name": tool_def.get("name", "unknown"),
                        "description": tool_def.get("description", ""),
                        "input_schema": tool_def.get("parameters", {"type": "object", "properties": {}})
                    })
        else:
            # Dict format: iterate over tools
            for tool_name, tool_def in tool_definitions.items():
                if "paradigms" in tool_def and "function_call" in tool_def["paradigms"]:
                    spec = tool_def["paradigms"]["function_call"]["spec"]
                    tools.append({
                        "name": spec.get("name", tool_name),
                        "description": spec.get("description", ""),
                        "input_schema": spec.get("parameters", {"type": "object", "properties": {}})
                    })
                else:
                    tools.append({
                        "name": tool_name,
                        "description": tool_def.get("description", ""),
                        "input_schema": tool_def.get("parameters", {"type": "object", "properties": {}})
                    })

        return tools
