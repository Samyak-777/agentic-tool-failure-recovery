"""Base Agent Interface for Evaluation Framework.

This module defines the abstract interface that all agents must implement.
Supports OpenAI, Anthropic, and VLLM-based models.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> Dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens
        }


@dataclass
class ToolCall:
    """Represents a single tool call."""
    tool_name: str
    arguments: Dict[str, Any]


@dataclass
class AgentAction:
    """Represents an action taken by the agent."""
    type: str  # "tool_call" or "final_answer"
    tool_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None
    content: Optional[str] = None  # For final_answer
    thought: Optional[str] = None  # Agent's reasoning
    tool_calls: Optional[List["ToolCall"]] = None  # For parallel tool calls


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def initialize(self, task_description: str, tool_definitions: Dict[str, Any]) -> None:
        """Initialize the agent with task and tool definitions.

        Args:
            task_description: The task to solve
            tool_definitions: Tool definitions (Function Calling or MCP format)
        """
        pass

    @abstractmethod
    def step(self, user_message: Optional[str] = None) -> AgentAction:
        """Execute one reasoning step.

        Args:
            user_message: Optional user message (used for initial task)

        Returns:
            AgentAction: The action taken by the agent
        """
        pass

    @abstractmethod
    def receive_tool_result(self, tool_name: str, result: Dict[str, Any]) -> None:
        """Receive the result of a tool call.

        Args:
            tool_name: Name of the tool that was called
            result: Result returned by the tool
        """
        pass

    @abstractmethod
    def get_total_tokens(self) -> int:
        """Get total tokens consumed.

        Returns:
            Total token count
        """
        pass

    @abstractmethod
    def get_token_usage(self) -> TokenUsage:
        """Get detailed token usage statistics.

        Returns:
            TokenUsage with input_tokens and output_tokens
        """
        pass

    @abstractmethod
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history.

        Returns:
            List of messages
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the agent state."""
        pass
