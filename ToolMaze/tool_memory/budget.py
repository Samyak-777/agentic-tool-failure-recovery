"""
Budget Tracker for Layer 3.
Monitors tool call limits, recovery steps, and token consumption against budgets.
"""

from dataclasses import dataclass

@dataclass
class BudgetConfig:
    max_total_tool_calls: int = 20
    max_recovery_attempts: int = 5
    max_retries_per_tool: int = 2

class BudgetTracker:
    """Enforces computational and execution limits across the recovery loop."""

    def __init__(self, config: BudgetConfig = BudgetConfig()):
        self.config = config
        self.total_tool_calls: int = 0
        self.recovery_attempts: int = 0
        self.tool_retry_counts: dict = {}

    def record_tool_call(self, tool_name: str, is_recovery: bool = False):
        self.total_tool_calls += 1
        if is_recovery:
            self.recovery_attempts += 1
            self.tool_retry_counts[tool_name] = self.tool_retry_counts.get(tool_name, 0) + 1

    def can_retry_tool(self, tool_name: str) -> bool:
        if self.total_tool_calls >= self.config.max_total_tool_calls:
            return False
        if self.recovery_attempts >= self.config.max_recovery_attempts:
            return False
        current_retries = self.tool_retry_counts.get(tool_name, 0)
        return current_retries <= self.config.max_retries_per_tool

    def has_recovery_budget(self) -> bool:
        return (
            self.total_tool_calls < self.config.max_total_tool_calls and
            self.recovery_attempts < self.config.max_recovery_attempts
        )

    def get_remaining_recovery_calls(self) -> int:
        return max(0, self.config.max_recovery_attempts - self.recovery_attempts)

    def reset(self):
        self.total_tool_calls = 0
        self.recovery_attempts = 0
        self.tool_retry_counts.clear()
