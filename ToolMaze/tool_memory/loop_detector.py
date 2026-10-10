"""
ToolMaze/tool_memory/loop_detector.py
Layer 6: Cost-Aware Control & Loop Detection

Detects repetitive and cyclic tool call patterns (immediate loops, ping-pong loops,
and multi-step cycles) to prevent runaway token spend and infinite agent deadlocks.
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple


@dataclass
class LoopCheckResult:
    """Outcome of loop inspection after a tool call."""
    is_loop: bool = False
    loop_type: str = "none"  # "immediate" | "ping_pong" | "cycle" | "none"
    involved_tools: List[str] = field(default_factory=list)
    suggested_action: str = "continue"  # "continue" | "blacklist_and_reroute" | "abort"
    warning_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_loop": self.is_loop,
            "loop_type": self.loop_type,
            "involved_tools": self.involved_tools,
            "suggested_action": self.suggested_action,
            "warning_message": self.warning_message,
        }


class LoopDetector:
    """Monitors sequence of tool invocations to identify unproductive cycles."""

    def __init__(self, max_consecutive_same_tool: int = 2, max_ping_pong_repeats: int = 2):
        self.max_consecutive_same_tool = max_consecutive_same_tool
        self.max_ping_pong_repeats = max_ping_pong_repeats
        self.call_history: List[Tuple[str, str, bool]] = []  # (tool_name, args_hash, is_valid)

    def record_call(self, tool_name: str, arguments: Dict[str, Any], is_valid: bool = True) -> LoopCheckResult:
        """Record an execution step and analyze history for loops."""
        args_hash = self._hash_args(arguments)
        self.call_history.append((tool_name, args_hash, is_valid))

        return self.check_loops()

    def check_loops(self) -> LoopCheckResult:
        """Inspect the current call history for loop patterns."""
        if len(self.call_history) < 2:
            return LoopCheckResult()

        # 1. Immediate Loop Check: Last N calls are the same tool
        immediate_result = self._check_immediate_loop()
        if immediate_result.is_loop:
            return immediate_result

        # 2. Ping-Pong Loop Check: Alternating between 2 tools (A -> B -> A -> B)
        ping_pong_result = self._check_ping_pong_loop()
        if ping_pong_result.is_loop:
            return ping_pong_result

        # 3. Generalized Cyclic Loop Check: (e.g. A -> B -> C -> A -> B -> C)
        cycle_result = self._check_cycle_loop()
        if cycle_result.is_loop:
            return cycle_result

        return LoopCheckResult()

    def _check_immediate_loop(self) -> LoopCheckResult:
        """Check if agent is repeatedly calling the same tool without progress."""
        if len(self.call_history) < self.max_consecutive_same_tool:
            return LoopCheckResult()

        recent = self.call_history[-self.max_consecutive_same_tool:]
        tool_names = [call[0] for call in recent]
        
        # If all recent calls are the same tool
        if len(set(tool_names)) == 1:
            tool_name = tool_names[0]
            # If at least one failed or args are identical
            args_hashes = [call[1] for call in recent]
            has_failures = any(not call[2] for call in recent)
            identical_args = len(set(args_hashes)) == 1

            if has_failures or identical_args:
                return LoopCheckResult(
                    is_loop=True,
                    loop_type="immediate",
                    involved_tools=[tool_name],
                    suggested_action="blacklist_and_reroute",
                    warning_message=(
                        f"Immediate loop detected: Tool '{tool_name}' called {self.max_consecutive_same_tool} "
                        "times consecutively without progress. Tool marked for rerouting."
                    )
                )

        return LoopCheckResult()

    def _check_ping_pong_loop(self) -> LoopCheckResult:
        """Check for alternating ping-pong patterns like A -> B -> A -> B."""
        # Need at least 4 calls for A -> B -> A -> B
        window = 4
        if len(self.call_history) < window:
            return LoopCheckResult()

        recent = [call[0] for call in self.call_history[-window:]]
        # Check if A == C and B == D and A != B
        if recent[0] == recent[2] and recent[1] == recent[3] and recent[0] != recent[1]:
            involved = [recent[0], recent[1]]
            return LoopCheckResult(
                is_loop=True,
                loop_type="ping_pong",
                involved_tools=involved,
                suggested_action="blacklist_and_reroute",
                warning_message=(
                    f"Ping-pong oscillation detected between '{involved[0]}' and '{involved[1]}'. "
                    "Break cyclic oscillation by forcing alternative path exploration."
                )
            )

        return LoopCheckResult()

    def _check_cycle_loop(self) -> LoopCheckResult:
        """Check for multi-step cycles: length 3 cycle repeated twice (A->B->C->A->B->C)."""
        window = 6
        if len(self.call_history) < window:
            return LoopCheckResult()

        recent = [call[0] for call in self.call_history[-window:]]
        # Check if [0,1,2] == [3,4,5]
        if recent[0:3] == recent[3:6] and len(set(recent[0:3])) == 3:
            involved = list(set(recent[0:3]))
            return LoopCheckResult(
                is_loop=True,
                loop_type="cycle",
                involved_tools=involved,
                suggested_action="abort",
                warning_message=(
                    f"Repetitive 3-step cycle detected across tools {involved}. "
                    "Aborting cyclic deadlock to preserve token budget."
                )
            )

        return LoopCheckResult()

    def _hash_args(self, args: Dict[str, Any]) -> str:
        """Compute deterministic hash of arguments dictionary."""
        try:
            serialized = json.dumps(args, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode('utf-8')).hexdigest()
        except Exception:
            return str(args)

    def reset(self):
        """Reset history."""
        self.call_history.clear()
