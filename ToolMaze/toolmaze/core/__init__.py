"""ToolMaze runtime core.

Exposes the two pieces evaluation depends on:
- ExecutionContext: per-run tool-call history and lookup helpers.
- ToolExecutor:     loads plugins from `tools/plugins/`, validates arguments,
                    executes, and records results into ExecutionContext.
"""

from .context import ExecutionContext
from .executor import ToolExecutor

__all__ = ["ExecutionContext", "ToolExecutor"]
