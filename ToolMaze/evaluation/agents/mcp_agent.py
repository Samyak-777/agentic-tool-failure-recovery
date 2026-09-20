"""MCP-based Agent implementation using prompt-based tool calling.

MCP (Model Context Protocol) style: tools are described in the system prompt,
and the model outputs tool calls as structured text (JSON blocks).
"""

import json
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI

from .base_agent import BaseAgent, AgentAction, TokenUsage


class MCPAgent(BaseAgent):
    """Agent implementation using MCP-style prompt-based tool calling.

    Instead of using native function calling APIs, tools are described in the
    system prompt and the model outputs tool calls as JSON blocks.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize MCP agent.

        Args:
            model: Model name
            api_key: API key
            base_url: Optional base URL (for VLLM or other OpenAI-compatible APIs)
            temperature: Sampling temperature
            max_tokens: Max tokens per response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize OpenAI-compatible client
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        # State
        self.messages: List[Dict[str, Any]] = []
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.task_description: str = ""
        self.mcp_tools_text: str = ""

    def initialize(self, task_description: str, tool_definitions: Dict[str, Any]) -> None:
        """Initialize with task and tools."""
        self.task_description = task_description
        self.messages = []
        self.input_tokens = 0
        self.output_tokens = 0

        # Extract MCP tool definitions (text format)
        self.mcp_tools_text = self._extract_mcp_definitions(tool_definitions)

        # Build and add system message
        system_message = self._build_system_message()
        self.messages.append({
            "role": "system",
            "content": system_message
        })

    def step(self, user_message: Optional[str] = None) -> AgentAction:
        """Execute one reasoning step."""
        # Add user message if provided
        if user_message:
            self.messages.append({
                "role": "user",
                "content": user_message
            })

        # Call LLM API (without tools parameter - MCP uses prompt-based approach)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Update token count
            if hasattr(response, 'usage') and response.usage:
                self.input_tokens += response.usage.prompt_tokens
                self.output_tokens += response.usage.completion_tokens

            # Get response content
            content = response.choices[0].message.content or ""

            # Add assistant message to history
            self.messages.append({
                "role": "assistant",
                "content": content
            })

            # Try to parse tool call from response
            tool_call = self._parse_tool_call(content)

            if tool_call:
                return AgentAction(
                    type="tool_call",
                    tool_name=tool_call["tool"],
                    arguments=tool_call["arguments"],
                    thought=self._extract_thought(content)
                )

            # No tool call found - treat as final answer
            return AgentAction(
                type="final_answer",
                content=content
            )

        except Exception as e:
            return AgentAction(
                type="final_answer",
                content=f"Error during execution: {str(e)}"
            )

    def receive_tool_result(self, tool_name: str, result: Dict[str, Any]) -> None:
        """Receive tool result and add to conversation as text."""
        # Format result as text message
        result_text = f"Tool `{tool_name}` returned:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```"

        self.messages.append({
            "role": "user",
            "content": result_text
        })

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

    def _extract_mcp_definitions(self, tool_definitions: Dict[str, Any]) -> str:
        """Extract MCP tool definitions text.

        Args:
            tool_definitions: Tool definitions from task JSON

        Returns:
            MCP tool definitions as text
        """
        # Handle list format (from _build_tool_definitions)
        if isinstance(tool_definitions, list):
            # Extract MCP text or generate from paradigms
            for tool_def in tool_definitions:
                mcp_text = tool_def.get("paradigms", {}).get("mcp", {}).get("prompt_signature", "")
                if mcp_text:
                    # Has MCP definitions, generate from all tools
                    return self._generate_mcp_from_paradigms(tool_definitions)
            # No MCP, fallback to generating from function_call specs
            return self._generate_mcp_from_paradigms(tool_definitions)

        # Check for direct mcp key
        if "mcp" in tool_definitions:
            return tool_definitions["mcp"]

        # Fallback: generate from function_call definitions
        if "function_call" in tool_definitions:
            return self._generate_mcp_from_fc(tool_definitions["function_call"])

        return ""

    def _generate_mcp_from_paradigms(self, tool_definitions: List[Dict[str, Any]]) -> str:
        """Generate MCP-style text from YAML tool definitions with paradigms structure.

        Args:
            tool_definitions: List of tool definitions from _build_tool_definitions

        Returns:
            MCP-style tool description text
        """
        lines = ["You have access to the following tools:\n"]

        for i, tool_def in enumerate(tool_definitions, 1):
            # Try MCP paradigm first
            mcp = tool_def.get("paradigms", {}).get("mcp", {})
            if mcp.get("prompt_signature") and mcp.get("prompt_description"):
                signature = mcp["prompt_signature"]
                desc = mcp["prompt_description"]
                lines.append(f"{i}. `{signature}`: {desc}\n")
            else:
                # Fallback: generate from function_call spec
                spec = tool_def.get("paradigms", {}).get("function_call", {}).get("spec", {})
                name = spec.get("name", tool_def.get("name", "unknown"))
                desc = spec.get("description", "")
                params = spec.get("parameters", {})
                props = params.get("properties", {})
                required = params.get("required", [])

                param_parts = []
                for pname, pdef in props.items():
                    ptype = pdef.get("type", "any")
                    if pname in required:
                        param_parts.append(f"{pname}: {ptype}")
                    else:
                        default = pdef.get("default", "None")
                        param_parts.append(f"{pname}: {ptype} = {default}")

                signature = f"{name}({', '.join(param_parts)}) -> dict"
                lines.append(f"{i}. `{signature}`: {desc}\n")

        return "\n".join(lines)

    def _generate_mcp_from_fc(self, fc_tools: List[Dict[str, Any]]) -> str:
        """Generate MCP-style text from function calling definitions.

        Args:
            fc_tools: List of function calling tool definitions

        Returns:
            MCP-style tool description text
        """
        lines = ["You have access to the following tools:\n"]

        for i, tool in enumerate(fc_tools, 1):
            func = tool.get("function", tool)
            name = func.get("name", "unknown")
            desc = func.get("description", "")
            params = func.get("parameters", {})

            # Build parameter signature
            props = params.get("properties", {})
            required = params.get("required", [])

            param_parts = []
            for pname, pdef in props.items():
                ptype = pdef.get("type", "any")
                if pname in required:
                    param_parts.append(f"{pname}: {ptype}")
                else:
                    default = pdef.get("default", "None")
                    param_parts.append(f"{pname}: {ptype} = {default}")

            signature = f"{name}({', '.join(param_parts)}) -> dict"
            lines.append(f"{i}. `{signature}`: {desc}\n")

        return "\n".join(lines)

    def _build_system_message(self) -> str:
        """Build system message with MCP tool definitions."""
        return f"""You are a helpful AI assistant that can use tools to solve tasks.

{self.mcp_tools_text}

## How to use tools

To use a tool, output a JSON block in the following format:
```json
{{
  "tool": "tool_name",
  "arguments": {{
    "param1": "value1",
    "param2": "value2"
  }}
}}
```

## Important guidelines

1. Think step by step about what information you need
2. Call tools one at a time and wait for results
3. If a tool fails, consider retrying or using alternative approaches
4. If a tool returns unexpected data, verify it makes sense before using it
5. When you have completed the task, provide a clear final answer WITHOUT using any tool call format

Always provide clear explanations of your reasoning and actions."""

    def _parse_tool_call(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse tool call from model output.

        Looks for JSON blocks in the format:
        ```json
        {"tool": "...", "arguments": {...}}
        ```

        Args:
            content: Model output text

        Returns:
            Parsed tool call dict or None if not found
        """
        # Pattern to match JSON code blocks
        json_pattern = r'```(?:json)?\s*\n?\s*(\{[\s\S]*?\})\s*\n?```'

        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                parsed = json.loads(match)
                # Check if it's a valid tool call format
                if "tool" in parsed and "arguments" in parsed:
                    return {
                        "tool": parsed["tool"],
                        "arguments": parsed.get("arguments", {})
                    }
            except json.JSONDecodeError:
                continue

        # Also try to find inline JSON (without code blocks)
        inline_pattern = r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^}]*\}\s*\}'
        inline_matches = re.findall(inline_pattern, content)

        for match in inline_matches:
            try:
                parsed = json.loads(match)
                if "tool" in parsed and "arguments" in parsed:
                    return {
                        "tool": parsed["tool"],
                        "arguments": parsed.get("arguments", {})
                    }
            except json.JSONDecodeError:
                continue

        return None

    def _extract_thought(self, content: str) -> Optional[str]:
        """Extract reasoning/thought from content before tool call.

        Args:
            content: Full model output

        Returns:
            Thought text or None
        """
        # Find the position of the first JSON block
        json_pattern = r'```(?:json)?\s*\n?\s*\{'
        match = re.search(json_pattern, content)

        if match:
            thought = content[:match.start()].strip()
            return thought if thought else None

        return None
