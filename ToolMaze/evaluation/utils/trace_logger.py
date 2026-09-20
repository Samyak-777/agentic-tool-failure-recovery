"""Trace Logger for recording agent execution."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class TraceLogger:
    """Records the complete execution trace of an agent."""

    def __init__(self, task_id: str, mode: str):
        """Initialize trace logger.

        Args:
            task_id: Task identifier
            mode: Perturbation mode (P0-P4)
        """
        self.task_id = task_id
        self.mode = mode
        self.messages: List[Dict[str, Any]] = []
        self._call_index = 0

    def log_user_message(self, content: str) -> None:
        """Log the initial user message."""
        self.messages.append({
            "role": "user",
            "content": content
        })

    def log_round(
        self,
        round_num: int,
        agent_action: Dict[str, Any],
        tool_result: Optional[Dict[str, Any]] = None,
        perturbation_status: str = "clean"
    ) -> None:
        """Log one round of interaction in role/content message format."""
        action_type = agent_action.get("type")
        thought = agent_action.get("thought") or ""
        content = agent_action.get("content") or thought

        # Build assistant message
        assistant_msg: Dict[str, Any] = {
            "role": "assistant",
            "type": action_type,
            "content": content
        }

        # Track tool call metadata
        call_id = None
        if action_type == "tool_call":
            self._call_index += 1
            call_id = f"call-{self._call_index}"
            assistant_msg["tool_call"] = {
                "id": call_id,
                "name": agent_action.get("tool_name"),
                "arguments": agent_action.get("arguments", {})
            }
            if thought:
                assistant_msg.setdefault("metadata", {})["thought"] = thought
        elif thought:
            assistant_msg.setdefault("metadata", {})["thought"] = thought

        self.messages.append(assistant_msg)

        # If tool result exists, log it as a tool message
        if tool_result is not None:
            tool_msg = {
                "role": "tool",
                "name": agent_action.get("tool_name"),
                "call_id": call_id or assistant_msg.get("tool_call", {}).get("id"),
                "content": tool_result,
                "metadata": {
                    "perturbation_status": perturbation_status
                }
            }
            self.messages.append(tool_msg)

    def to_dict(
        self,
        token_usage: Optional[Dict[str, int]] = None,
        judgement: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert trace to dictionary.

        Args:
            token_usage: Token usage dict with input_tokens, output_tokens, total_tokens
            judgement: Judgement result with pass, failure_reason, trace_check

        Returns:
            Dictionary representation of the trace
        """
        result = {
            "task_id": self.task_id,
            "mode": self.mode,
        }

        # Add judgement fields if provided
        if judgement:
            result["pass"] = judgement.get("pass", False)
            result["failure_reason"] = judgement.get("failure_reason")
            result["trace_check"] = judgement.get("trace_check", {})


        # Add token usage
        if token_usage:
            result["tokens"] = token_usage
        else:
            result["tokens"] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }

        # Messages at the end
        result["messages"] = self.messages

        return result

    def to_summary(self) -> str:
        """Generate human-readable text summary.

        Returns:
            Text summary of the trace
        """
        lines = [
            f"Task: {self.task_id}",
            f"Mode: {self.mode}",
            f"Total Messages: {len(self.messages)}",
            "",
            "Execution Trace:"
        ]

        for msg in self.messages:
            if msg["role"] == "user":
                lines.append("\nUser:")
                lines.append(f"  {msg.get('content', '')[:200]}")
            elif msg["role"] == "assistant":
                msg_type = msg.get("type", "message")
                if msg_type == "tool_call":
                    lines.append("\nAssistant (tool_call):")
                    if msg.get("content"):
                        lines.append(f"  Thought: {msg.get('content', '')[:200]}")
                    call = msg.get("tool_call", {})
                    lines.append(f"  Tool: {call.get('name')} Args: {json.dumps(call.get('arguments', {}), ensure_ascii=False)}")
                elif msg_type == "final_answer":
                    lines.append("\nAssistant (final):")
                    lines.append(f"  {msg.get('content', '')[:200]}")
                else:
                    lines.append("\nAssistant:")
                    lines.append(f"  {msg.get('content', '')[:200]}")
            elif msg["role"] == "tool":
                lines.append("\nTool Response:")
                lines.append(f"  Tool: {msg.get('name')} ({msg.get('metadata', {}).get('perturbation_status')})")
                lines.append(f"  Output: {json.dumps(msg.get('content', {}), ensure_ascii=False)[:200]}")

        return "\n".join(lines)

    def save(
        self,
        filepath: Path,
        token_usage: Optional[Dict[str, int]] = None,
        judgement: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save trace to JSON file.

        Args:
            filepath: Path to save the trace
            token_usage: Token usage dict
            judgement: Judgement result
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(token_usage, judgement), f, indent=2, ensure_ascii=False)
