"""Agent implementations for evaluation framework."""

from .base_agent import BaseAgent, AgentAction, TokenUsage, ToolCall

# Lazy imports to avoid dependency errors when not using specific agents
def __getattr__(name):
    if name == "OpenAIAgent":
        from .openai_agent import OpenAIAgent
        return OpenAIAgent
    elif name == "AnthropicAgent":
        from .anthropic_agent import AnthropicAgent
        return AnthropicAgent
    elif name == "VLLMAgent":
        from .vllm_agent import VLLMAgent
        return VLLMAgent
    elif name == "MCPAgent":
        from .mcp_agent import MCPAgent
        return MCPAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BaseAgent",
    "AgentAction",
    "TokenUsage",
    "OpenAIAgent",
    "AnthropicAgent",
    "VLLMAgent",
    "MCPAgent"
]
