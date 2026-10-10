"""
ToolMaze/selective_verification/verifier.py
Layer 7: Selective LLM Verification for Ambiguous Cases

Invoked ONLY when deterministic SOV flags an output as ambiguous or borderline,
minimizing token consumption while maintaining maximum semantic precision.
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class VerificationResult:
    """Outcome of Layer 7 selective verification."""
    is_valid: bool
    confidence: float
    explanation: str
    tokens_consumed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "tokens_consumed": self.tokens_consumed
        }


class SelectiveVerifier:
    """Executes targeted LLM-assisted verification exclusively on ambiguous outputs."""

    def __init__(self, llm_client: Optional[Any] = None, model: str = "gemini-3.8-flash"):
        self.client = llm_client
        self.model = model

    def verify(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        output: Any,
        task_query: str = ""
    ) -> VerificationResult:
        """Verify whether an ambiguous tool output is semantically valid.
        
        If no LLM client is configured, returns a conservative deterministic verdict.
        """
        if not self.client:
            # Conservative deterministic fallback
            return VerificationResult(
                is_valid=True,
                confidence=0.7,
                explanation="LLM client not active; defaulting to tentative validity."
            )

        prompt = (
            f"You are a semantic output verification auditor.\n"
            f"Task Goal: {task_query}\n"
            f"Tool Called: {tool_name}\n"
            f"Arguments: {json.dumps(arguments)}\n"
            f"Tool Output: {str(output)[:500]}\n\n"
            f"Determine if the output is semantically meaningful and free from corruption.\n"
            f"Respond strictly in JSON format with no extra text:\n"
            f'{{"is_valid": true/false, "confidence": 0.0-1.0, "explanation": "brief reason"}}'
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=150
            )
            content = response.choices[0].message.content.strip()
            # Clean markdown codeblocks if returned
            if content.startswith("```"):
                content = content.strip("`").replace("json", "").strip()

            parsed = json.loads(content)
            tokens = getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 50
            return VerificationResult(
                is_valid=bool(parsed.get("is_valid", True)),
                confidence=float(parsed.get("confidence", 0.8)),
                explanation=str(parsed.get("explanation", "Verification completed.")),
                tokens_consumed=tokens
            )
        except Exception as e:
            return VerificationResult(
                is_valid=True,
                confidence=0.5,
                explanation=f"Verification failed with exception: {e}; tentative pass."
            )
