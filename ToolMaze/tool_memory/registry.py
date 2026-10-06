"""
Tool Health Registry for Layer 3.
Tracks the operational health status and failure history of tools across
an execution trajectory.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

class ToolHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLACKLISTED = "blacklisted"

@dataclass
class ToolRecord:
    tool_name: str
    status: ToolHealthStatus = ToolHealthStatus.HEALTHY
    total_calls: int = 0
    consecutive_failures: int = 0
    total_failures: int = 0
    last_error_category: Optional[str] = None
    blacklist_reason: Optional[str] = None
    last_called_timestamp: float = field(default_factory=time.time)

class ToolHealthRegistry:
    """Maintains stateful health tracking for all tools invoked in a task."""

    def __init__(self, failure_threshold_to_blacklist: int = 2):
        self.failure_threshold = failure_threshold_to_blacklist
        self.tools: Dict[str, ToolRecord] = {}

    def get_record(self, tool_name: str) -> ToolRecord:
        if tool_name not in self.tools:
            self.tools[tool_name] = ToolRecord(tool_name=tool_name)
        return self.tools[tool_name]

    def record_success(self, tool_name: str):
        record = self.get_record(tool_name)
        record.total_calls += 1
        record.consecutive_failures = 0
        if record.status == ToolHealthStatus.DEGRADED:
            record.status = ToolHealthStatus.HEALTHY
        record.last_called_timestamp = time.time()

    def record_failure(self, tool_name: str, category: str, is_permanent: bool = False):
        record = self.get_record(tool_name)
        record.total_calls += 1
        record.consecutive_failures += 1
        record.total_failures += 1
        record.last_error_category = category
        record.last_called_timestamp = time.time()

        if is_permanent or record.consecutive_failures >= self.failure_threshold:
            record.status = ToolHealthStatus.BLACKLISTED
            record.blacklist_reason = (
                f"Permanent fault inferred" if is_permanent 
                else f"Exceeded consecutive failure threshold ({record.consecutive_failures})"
            )
        else:
            record.status = ToolHealthStatus.DEGRADED

    def is_blacklisted(self, tool_name: str) -> bool:
        return self.get_record(tool_name).status == ToolHealthStatus.BLACKLISTED

    def get_blacklisted_tools(self) -> List[str]:
        return [name for name, r in self.tools.items() if r.status == ToolHealthStatus.BLACKLISTED]

    def reset(self):
        self.tools.clear()
