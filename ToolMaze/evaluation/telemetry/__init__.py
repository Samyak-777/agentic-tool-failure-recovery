"""
ToolMaze Telemetry Package.

Provides persistent structured execution logging, perturbation tracking,
and causal failure attribution.
"""

from .schema import (
    TelemetryEvent,
    EventType,
    SCHEMA_VERSION,
    CausalAttribution,
    sanitize_and_redact
)
from .perturbation_tracker import PerturbationTracker
from .recorder import (
    TelemetryManager,
    TelemetryRecorder,
    get_project_root
)

__all__ = [
    "TelemetryEvent",
    "EventType",
    "SCHEMA_VERSION",
    "CausalAttribution",
    "sanitize_and_redact",
    "PerturbationTracker",
    "TelemetryManager",
    "TelemetryRecorder",
    "get_project_root"
]
