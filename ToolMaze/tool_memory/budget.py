"""
Budget Tracker for Layer 3.
Monitors tool call limits, recovery steps, and token consumption against budgets.

Fix #12: Dynamic topology-aware budget — C1=20, C2=25, C3=35, C4=40 tool calls.
"""

from dataclasses import dataclass


# Topology-aware budget presets (Fix #12)
TOPOLOGY_BUDGETS = {
    "c1": {"max_total_tool_calls": 20, "max_recovery_attempts": 6,  "max_retries_per_tool": 2},
    "c2": {"max_total_tool_calls": 25, "max_recovery_attempts": 8,  "max_retries_per_tool": 2},
    "c3": {"max_total_tool_calls": 35, "max_recovery_attempts": 10, "max_retries_per_tool": 2},
    "c4": {"max_total_tool_calls": 40, "max_recovery_attempts": 12, "max_retries_per_tool": 2},
}


@dataclass
class BudgetConfig:
    max_total_tool_calls: int = 20
    max_recovery_attempts: int = 5
    max_retries_per_tool: int = 2


def get_topology_budget(topology: str = "c1") -> BudgetConfig:
    """Return a BudgetConfig pre-tuned for the given topology complexity."""
    preset = TOPOLOGY_BUDGETS.get(topology.lower(), TOPOLOGY_BUDGETS["c1"])
    return BudgetConfig(**preset)


class BudgetTracker:
    """Enforces computational and execution limits across the recovery loop."""

    def __init__(self, config: BudgetConfig = BudgetConfig()):
        self.config = config
        self.total_tool_calls: int = 0
        self.recovery_attempts: int = 0
        self.tool_retry_counts: dict = {}
        self.steps_completed: int = 0      # Fix #13: track partial progress
        self.steps_required: int = 0       # Fix #13: total expected steps

    def record_tool_call(self, tool_name: str, is_recovery: bool = False):
        self.total_tool_calls += 1
        if is_recovery:
            self.recovery_attempts += 1
            self.tool_retry_counts[tool_name] = self.tool_retry_counts.get(tool_name, 0) + 1

    def record_step_completed(self):
        """Fix #13: Record a successfully completed DAG step."""
        self.steps_completed += 1

    def set_total_steps(self, n: int):
        """Fix #13: Set expected total steps from task DAG."""
        self.steps_required = n

    def get_partial_progress(self) -> float:
        """Fix #13: Return PRP = steps_completed / steps_required (0.0 to 1.0)."""
        if self.steps_required <= 0:
            return 0.0
        return min(1.0, self.steps_completed / self.steps_required)

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
        self.steps_completed = 0
        self.steps_required = 0
