"""
Tool Memory Store for Layer 3.
Maintains input signature history, cached outputs, and execution checkpoints.

Fix #10: Added ExecutionCheckpoint and checkpoint tracking for backtrack/replay on rerouting.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class ExecutionCheckpoint:
    """Execution checkpoint saved at each valid DAG step (Fix #10)."""
    step_num: int
    tool_name: str
    arguments: Dict[str, Any]
    output: Any
    is_valid: bool
    executed_tools: List[str] = field(default_factory=list)


class ToolMemory:
    """Stores execution history, argument signatures, cached outputs, and checkpoints."""

    def __init__(self):
        # Maps tool_name -> list of stringified argument signatures tried
        self.tried_signatures: Dict[str, List[str]] = {}
        # Maps tool_name -> list of outputs returned
        self.cached_outputs: Dict[str, List[Dict[str, Any]]] = {}
        # Chronological execution log
        self.call_log: List[Dict[str, Any]] = []
        # Fix #10: Checkpoints for backtrack replay
        self.checkpoints: List[ExecutionCheckpoint] = []

    def _hash_args(self, arguments: Dict[str, Any]) -> str:
        """Create a deterministic string signature for arguments."""
        try:
            return json.dumps(arguments, sort_keys=True)
        except Exception:
            return str(sorted(arguments.items()))

    def record_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        output: Any,
        is_valid: bool,
        step_num: int
    ):
        sig = self._hash_args(arguments)
        if tool_name not in self.tried_signatures:
            self.tried_signatures[tool_name] = []
        self.tried_signatures[tool_name].append(sig)

        if tool_name not in self.cached_outputs:
            self.cached_outputs[tool_name] = []
        self.cached_outputs[tool_name].append({
            "step": step_num,
            "arguments": arguments,
            "output": output,
            "is_valid": is_valid
        })

        self.call_log.append({
            "step": step_num,
            "tool_name": tool_name,
            "arguments": arguments,
            "is_valid": is_valid
        })

        # Fix #10: Save checkpoint for valid steps
        if is_valid:
            self.checkpoints.append(
                ExecutionCheckpoint(
                    step_num=step_num,
                    tool_name=tool_name,
                    arguments=arguments,
                    output=output,
                    is_valid=True,
                    executed_tools=self.get_executed_tools()
                )
            )

    def has_tried_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Check if these exact arguments have already been tried on this tool."""
        if tool_name not in self.tried_signatures:
            return False
        sig = self._hash_args(arguments)
        return sig in self.tried_signatures[tool_name]

    def get_latest_valid_output(self, tool_name: str) -> Optional[Any]:
        """Fetch the most recent valid output for a tool."""
        if tool_name not in self.cached_outputs:
            return None
        valid_entries = [e for e in self.cached_outputs[tool_name] if e.get("is_valid")]
        if valid_entries:
            return valid_entries[-1].get("output")
        return None

    def get_available_outputs(self) -> Dict[str, Any]:
        """Return the latest valid output for every successfully executed tool."""
        available_outputs = {}

        for tool_name in self.cached_outputs:
            output = self.get_latest_valid_output(tool_name)
            if output is not None:
                available_outputs[tool_name] = output

        return available_outputs
    
    def get_executed_tools(self) -> List[str]:
        """Return list of distinct tool names executed so far in chronological order."""
        seen = set()
        ordered = []
        for entry in self.call_log:
            t = entry.get("tool_name")
            if t and t not in seen:
                seen.add(t)
                ordered.append(t)
        return ordered

    def get_tool_history(self, tool_name: str) -> List[Dict[str, Any]]:
        """Return full history of calls for a specific tool."""
        return self.cached_outputs.get(tool_name, [])

    # Fix #10: Checkpoint query methods
    def get_latest_checkpoint(self) -> Optional[ExecutionCheckpoint]:
        """Fetch the most recent valid execution checkpoint."""
        return self.checkpoints[-1] if self.checkpoints else None

    def get_checkpoints(self) -> List[ExecutionCheckpoint]:
        """Return all checkpoints in chronological order."""
        return list(self.checkpoints)

    def get_checkpoint_for_tool(self, tool_name: str) -> Optional[ExecutionCheckpoint]:
        """Fetch the latest valid checkpoint for a specific tool."""
        for cp in reversed(self.checkpoints):
            if cp.tool_name == tool_name:
                return cp
        return None

    def reset(self):
        self.tried_signatures.clear()
        self.cached_outputs.clear()
        self.call_log.clear()
        self.checkpoints.clear()
