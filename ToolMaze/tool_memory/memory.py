"""
Tool Memory Store for Layer 3.
Maintains input signature history and cached outputs across execution steps.
"""

import json
from typing import Dict, Any, List, Optional

class ToolMemory:
    """Stores execution history, argument signatures, and cached outputs."""

    def __init__(self):
        # Maps tool_name -> list of stringified argument signatures tried
        self.tried_signatures: Dict[str, List[str]] = {}
        # Maps tool_name -> list of outputs returned
        self.cached_outputs: Dict[str, List[Dict[str, Any]]] = {}
        # Chronological execution log
        self.call_log: List[Dict[str, Any]] = []

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

    def reset(self):
        self.tried_signatures.clear()
        self.cached_outputs.clear()
        self.call_log.clear()
