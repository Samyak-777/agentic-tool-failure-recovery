"""
Structured Diagnosis Engine for Layer 2.
Translates Layer 1 SOV validation outputs and execution errors into
actionable, structured diagnoses.
"""

from typing import Dict, Any, List, Optional
from .taxonomy import (
    FailureCategory,
    PersistenceType,
    RecoveryDirective,
    StructuredDiagnosis
)

class StructuredDiagnosisEngine:
    """Diagnoses tool execution anomalies and infers root causes."""

    def __init__(self, max_transient_retries: int = 2):
        self.max_transient_retries = max_transient_retries

    def diagnose(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        raw_result: Any,
        validation_result: Optional[Dict[str, Any]] = None,
        tool_call_history: Optional[List[Dict[str, Any]]] = None,
        step_num: int = 1
    ) -> StructuredDiagnosis:
        """Perform comprehensive structured diagnosis on a tool return.
        
        Args:
            tool_name: Name of tool executed
            arguments: Arguments supplied by agent
            raw_result: The raw return payload or error dict
            validation_result: Layer 1 SOV validation dictionary (if any)
            tool_call_history: Prior calls to this tool within current task
            step_num: Current execution step number
            
        Returns:
            StructuredDiagnosis dataclass
        """
        history = tool_call_history or []
        prior_calls = [h for h in history if h.get("tool_name") == tool_name]
        prior_failures = [h for h in prior_calls if not h.get("is_valid", True)]
        failure_count = len(prior_failures)

        # Case 1: Raw Execution Exception (e.g. HTTP 404, 500, network crash)
        if isinstance(raw_result, dict) and ("error" in raw_result or raw_result.get("status") == "error"):
            err_str = str(raw_result.get("error", raw_result.get("message", ""))).lower()
            return self._diagnose_execution_error(
                tool_name=tool_name,
                arguments=arguments,
                error_str=err_str,
                raw_result=raw_result,
                failure_count=failure_count,
                step_num=step_num
            )

        # Case 2: Layer 1 SOV Anomaly Detected (P3/P4 Semantic Corruption)
        if validation_result and validation_result.get("pipeline_status") == "INVALID":
            return self._diagnose_sov_anomaly(
                tool_name=tool_name,
                arguments=arguments,
                raw_result=raw_result,
                validation_result=validation_result,
                failure_count=failure_count,
                step_num=step_num
            )

        # Case 3: Empty Payload Anomaly
        if raw_result is None or raw_result == {} or raw_result == []:
            return StructuredDiagnosis(
                tool_name=tool_name,
                is_valid=False,
                category=FailureCategory.EMPTY_PAYLOAD_ANOMALY,
                persistence=PersistenceType.TRANSIENT if failure_count == 0 else PersistenceType.PERMANENT,
                root_cause="Tool executed successfully but returned an empty response body.",
                severity="MEDIUM",
                recommended_action=RecoveryDirective.RETRY if failure_count == 0 else RecoveryDirective.REROUTE,
                step_num=step_num
            )

        # Case 4: Branch 1 - Valid Execution
        return StructuredDiagnosis(
            tool_name=tool_name,
            is_valid=True,
            category=FailureCategory.SYNTAX_SCHEMA_ERROR,  # unused for valid
            persistence=PersistenceType.TRANSIENT,
            root_cause="Clean execution; passed all deterministic checks.",
            severity="LOW",
            recommended_action=RecoveryDirective.CONTINUE,
            step_num=step_num
        )

    def _diagnose_execution_error(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        error_str: str,
        raw_result: Any,
        failure_count: int,
        step_num: int
    ) -> StructuredDiagnosis:
        """Diagnose explicit system/HTTP errors (P1 / P2)."""
        # 404 / Not Found / Method Not Allowed -> Permanent
        if "404" in error_str or "not found" in error_str:
            return StructuredDiagnosis(
                tool_name=tool_name,
                is_valid=False,
                category=FailureCategory.EXTERNAL_SERVICE_ERROR,
                persistence=PersistenceType.PERMANENT,
                root_cause="Endpoint or target resource not found (HTTP 404).",
                severity="HIGH",
                recommended_action=RecoveryDirective.REROUTE,
                raw_error=raw_result,
                step_num=step_num
            )

        # 429 / Rate Limit / 503 / 502 -> Transient
        if "429" in error_str or "503" in error_str or "502" in error_str or "timeout" in error_str or "temporar" in error_str:
            if failure_count < self.max_transient_retries:
                persistence = PersistenceType.TRANSIENT
                action = RecoveryDirective.RETRY
            else:
                persistence = PersistenceType.PERMANENT
                action = RecoveryDirective.REROUTE

            return StructuredDiagnosis(
                tool_name=tool_name,
                is_valid=False,
                category=FailureCategory.EXTERNAL_SERVICE_ERROR,
                persistence=persistence,
                root_cause=f"External service rate limit or temporary outage: {error_str}",
                severity="MEDIUM",
                recommended_action=action,
                raw_error=raw_result,
                step_num=step_num
            )

        # Default execution failure
        persistence = PersistenceType.PERMANENT if failure_count > 0 else PersistenceType.TRANSIENT
        action = RecoveryDirective.REROUTE if persistence == PersistenceType.PERMANENT else RecoveryDirective.RETRY
        return StructuredDiagnosis(
            tool_name=tool_name,
            is_valid=False,
            category=FailureCategory.EXTERNAL_SERVICE_ERROR,
            persistence=persistence,
            root_cause=f"Tool runtime exception: {error_str}",
            severity="HIGH",
            recommended_action=action,
            raw_error=raw_result,
            step_num=step_num
        )

    def _diagnose_sov_anomaly(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        raw_result: Any,
        validation_result: Dict[str, Any],
        failure_count: int,
        step_num: int
    ) -> StructuredDiagnosis:
        """Diagnose semantic corruptions caught by Layer 1 SOV (P3 / P4)."""
        failed_checks = validation_result.get("failed_checks", [])
        violations = validation_result.get("violations", [])
        reason = validation_result.get("reason", "")
        
        # Identify dominant checker violation
        category = FailureCategory.SEMANTIC_RANGE_ERROR
        all_checker_names = list(failed_checks) + [v.get("checker", v.get("checker_name", "")) for v in violations]
        
        if any("schema" in c for c in all_checker_names):
            category = FailureCategory.SYNTAX_SCHEMA_ERROR
        elif any("type" in c for c in all_checker_names):
            category = FailureCategory.SYNTAX_SCHEMA_ERROR
        elif any("temporal" in c for c in all_checker_names):
            category = FailureCategory.TEMPORAL_SEQUENCE_ERROR
        elif any("entity" in c for c in all_checker_names):
            category = FailureCategory.ENTITY_CONTEXT_MISMATCH
        elif any("cross_tool" in c for c in all_checker_names):
            category = FailureCategory.CROSS_TOOL_CONFLICT
        elif any("cross_field" in c for c in all_checker_names):
            category = FailureCategory.CROSS_FIELD_CONFLICT
        elif any("range" in c for c in all_checker_names):
            category = FailureCategory.SEMANTIC_RANGE_ERROR

        # Determine persistence:
        # In ToolMaze P3 is transient (first call corrupt, second call clean)
        # P4 is permanent (all calls corrupt)
        # If this is the FIRST failure, infer TRANSIENT (retry once).
        # If this tool has ALREADY failed with semantic anomaly, infer PERMANENT (reroute).
        if failure_count == 0:
            persistence = PersistenceType.TRANSIENT
            action = RecoveryDirective.RETRY
            root_cause = f"Detected semantic output anomaly on first touch [{category.value}]. Candidate transient glitch."
        else:
            persistence = PersistenceType.PERMANENT
            action = RecoveryDirective.REROUTE
            root_cause = f"Persistent semantic anomaly on [{category.value}] across {failure_count+1} attempts."

        return StructuredDiagnosis(
            tool_name=tool_name,
            is_valid=False,
            category=category,
            persistence=persistence,
            root_cause=root_cause,
            severity="CRITICAL" if persistence == PersistenceType.PERMANENT else "HIGH",
            recommended_action=action,
            violations=violations,
            raw_error=raw_result,
            step_num=step_num
        )
