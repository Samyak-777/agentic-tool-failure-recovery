"""
Telemetry Event Schema and Data Models for ToolMaze Execution.
Schema Version: 1.0.0
"""

import os
import json
import uuid
import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional, List, Union


SCHEMA_VERSION = "1.0.0"

SENSITIVE_KEY_SUBSTRINGS = (
    "api_key", "apikey", "secret", "token", "password", "auth", "credential", "bearer"
)


def sanitize_and_redact(data: Any, max_string_len: int = 2000, depth: int = 0) -> Any:
    """Recursively redact secrets, truncate overly large strings, and guarantee JSON-serializability."""
    if depth > 10:
        return "<max_depth_exceeded>"

    if data is None or isinstance(data, (int, float, bool)):
        return data

    if isinstance(data, str):
        if len(data) > max_string_len:
            return data[:max_string_len] + f"... <truncated, total {len(data)} chars>"
        return data

    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            k_str = str(k)
            k_lower = k_str.lower()
            # Do not redact LLM metric token counts like "tokens", "total_tokens", "input_tokens", etc.
            is_token_count = ("tokens" in k_lower)
            if not is_token_count and any(s in k_lower for s in SENSITIVE_KEY_SUBSTRINGS):
                sanitized[k_str] = "[REDACTED]"
            else:
                sanitized[k_str] = sanitize_and_redact(v, max_string_len=max_string_len, depth=depth + 1)
        return sanitized

    if isinstance(data, (list, tuple, set)):
        return [sanitize_and_redact(item, max_string_len=max_string_len, depth=depth + 1) for item in data]

    # Custom object fallback
    if hasattr(data, "to_dict") and callable(getattr(data, "to_dict")):
        try:
            return sanitize_and_redact(data.to_dict(), max_string_len=max_string_len, depth=depth + 1)
        except Exception:
            pass

    return str(data)


class EventType(str, Enum):
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_INTERRUPTED = "run_interrupted"
    
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    INITIAL_PLAN_CREATED = "initial_plan_created"

    TOOL_CALL_STARTED = "tool_call_started"
    TOOL_CALL_COMPLETED = "tool_call_completed"
    TOOL_CALL_FAILED = "tool_call_failed"

    PERTURBATION_ELIGIBLE = "perturbation_eligible"
    PERTURBATION_ACTIVATED = "perturbation_activated"

    VALIDATION_COMPLETED = "validation_completed"
    DIAGNOSIS_COMPLETED = "diagnosis_completed"
    RECOVERY_STARTED = "recovery_started"

    CANDIDATE_PATHS_GENERATED = "candidate_paths_generated"
    PATH_PRUNED = "path_pruned"
    PATH_SELECTED = "path_selected"
    RECOVERY_COMPLETED = "recovery_completed"


class CausalAttribution(str, Enum):
    NOT_ACTIVATED = "perturbation_not_activated"
    ACTIVATED_NO_CHANGE = "perturbation_activated_no_observable_change"
    CHANGED_NO_FAILURE = "perturbation_changed_execution_no_failure"
    CHANGED_FAILURE_UNCERTAIN = "perturbation_changed_failure_attribution_uncertain"
    EVIDENCED_PERTURBATION_RELATED = "failure_supported_by_evidence_as_perturbation_related"
    FAILURE_UNRELATED = "failure_unrelated_to_observed_perturbation"
    INSUFFICIENT_TELEMETRY = "insufficient_telemetry_to_determine_attribution"


@dataclass
class TelemetryEvent:
    schema_version: str = SCHEMA_VERSION
    run_id: str = "unknown_run"
    task_id: str = "unknown_task"
    agent_type: str = "unknown_agent"
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    sequence_number: int = 0
    attempt_id: int = 1
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    event_type: str = EventType.TOOL_CALL_STARTED.value
    component: str = "core"
    status: str = "info"
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return sanitize_and_redact(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
