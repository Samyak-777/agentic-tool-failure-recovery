"""VLLM-based Agent implementation (OpenAI-compatible API)."""

from .openai_agent import OpenAIAgent


class VLLMAgent(OpenAIAgent):
    """Agent implementation for VLLM-deployed models using OpenAI-compatible API.

    This is essentially an OpenAI agent with custom base_url.
    VLLM provides OpenAI-compatible endpoints.
    """

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: str = "EMPTY",  # VLLM often uses dummy API key
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Initialize VLLM agent.

        Args:
            model: Model name deployed in VLLM
            base_url: VLLM server URL (e.g., http://localhost:8000/v1)
            api_key: API key (often "EMPTY" for VLLM)
            temperature: Sampling temperature
            max_tokens: Max tokens per response
        """
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens
        )
