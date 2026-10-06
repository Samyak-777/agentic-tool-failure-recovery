"""
Failure Taxonomy and Structured Diagnosis Models for Layer 2.
Categorizes failure types, infers persistence (Transient vs Permanent),
and attributes root causes.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time

class FailureCategory(str, Enum):
    """Hierarchical taxonomy of tool failure modes."""
    SYNTAX_SCHEMA_ERROR = "syntax_schema_error"
    SEMANTIC_RANGE_ERROR = "semantic_range_error"
    TEMPORAL_SEQUENCE_ERROR = "temporal_sequence_error"
    ENTITY_CONTEXT_MISMATCH = "entity_context_mismatch"
    CROSS_FIELD_CONFLICT = "cross_field_conflict"
    CROSS_TOOL_CONFLICT = "cross_tool_conflict"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    EMPTY_PAYLOAD_ANOMALY = "empty_payload_anomaly"
    DEPENDENCY_BROKEN = "dependency_broken"
    UNKNOWN_FAILURE = "unknown_failure"


class PersistenceType(str, Enum):
    """Inferred persistence of the anomaly."""
    TRANSIENT = "transient"      # P1 / P3 or transient glitch; eligible for immediate retry
    PERMANENT = "permanent"      # P2 / P4 or persistent bug; requires rerouting
    UNCERTAIN = "uncertain"      # Requires verification or 1 test retry


class RecoveryDirective(str, Enum):
    """Action pathway recommended by the diagnosis and memory layers."""
    CONTINUE = "continue"   # Branch 1: Valid
    RETRY = "retry"         # Transient glitch
    VERIFY = "verify"       # Ambiguous semantic result
    REROUTE = "reroute"     # Permanent failure, query alternative tool
    ABORT = "abort"         # Budget exhausted or unrecoverable


@dataclass
class StructuredDiagnosis:
    """Formal diagnosis emitted by Layer 2."""
    tool_name: str
    is_valid: bool
    category: FailureCategory
    persistence: PersistenceType
    root_cause: str
    severity: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    recommended_action: RecoveryDirective
    violations: List[Dict[str, Any]] = field(default_factory=list)
    raw_error: Optional[Any] = None
    step_num: int = 0
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "is_valid": self.is_valid,
            "category": self.category.value,
            "persistence": self.persistence.value,
            "root_cause": self.root_cause,
            "severity": self.severity,
            "recommended_action": self.recommended_action.value,
            "violations": self.violations,
            "confidence": self.confidence,
            "step_num": self.step_num,
            "timestamp": self.timestamp,
        }

    def format_agent_feedback(self) -> str:
        """Construct human/LLM-readable diagnostic feedback."""
        if self.is_valid:
            return f"Tool '{self.tool_name}' executed cleanly."
        
        lines = [
            f"=== ⚠️ STRUCTURED FAILURE DIAGNOSIS ===",
            f"Tool: {self.tool_name}",
            f"Failure Category: {self.category.value}",
            f"Persistence Type: {self.persistence.value.upper()}",
            f"Root Cause: {self.root_cause}",
            f"Recommended Action: {self.recommended_action.value.upper()}"
        ]
        if self.violations:
            lines.append("Violations Detected:")
            for v in self.violations:
                checker = v.get("checker", v.get("checker_name", "unknown"))
                msg = v.get("message", "unknown violation")
                lines.append(f"  - [{checker}] {msg}")
        return "\n".join(lines)
