"""
semantic_validation/checkers/temporal_checker.py

Checker 5 (L5): Temporal Consistency Checker.

Validates timestamp and date fields in tool outputs:
    1. Parseability: timestamps must parse according to standard formats (ISO-8601, YYYY-MM-DD, HH:MM).
    2. Future timestamp check: flags dates impossibly far in the future.
    3. Stale timestamp check: flags data older than max_timestamp_age_seconds if configured.

Rules:
    - If output is not a dict: INVALID.
    - If output contains "error": NOT_APPLICABLE.
    - If no temporal fields are present in output: NOT_APPLICABLE.
    - If temporal field fails parsing: INVALID (malformed timestamp).
    - If max_timestamp_age_seconds exceeded: INVALID (stale timestamp).
    - Otherwise: VALID.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..config.validation_config import TemporalConfig
from ..core.result import CheckResult
from ..core.status import CheckerStatus
from ..core.state_store import ExecutionValidationState
from .base import BaseChecker


TEMPORAL_FIELD_PATTERNS = [
    r"^.*timestamp.*$",
    r"^.*date.*$",
    r"^.*time.*$",
    r"^created_at$",
    r"^updated_at$",
    r"^check_in$",
    r"^check_out$",
    r"^departure.*$",
    r"^arrival.*$",
]

ISO_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%H:%M:%S",
    "%H:%M",
]


class TemporalChecker(BaseChecker):
    """L5: Checks formatting and validity of date/time fields."""

    name: str = "temporal"

    def __init__(self, config: Optional[TemporalConfig] = None) -> None:
        self.config = config or TemporalConfig()

    def check(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        state: Optional[ExecutionValidationState] = None,
        context: Optional[Any] = None,
    ) -> CheckResult:
        if not isinstance(result, dict):
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason=f"Tool output must be a dict, got {type(result).__name__}",
                details={"actual_type": type(result).__name__},
            )

        if "error" in result:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason="Tool returned an explicit error response; temporal check does not apply",
                details={"error": str(result.get("error"))},
            )

        temporal_fields = self._find_temporal_fields(result)
        if not temporal_fields:
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.NOT_APPLICABLE,
                reason=f"No temporal fields found in output for tool '{tool_name}'",
                details={"tool_name": tool_name},
            )

        violations: List[Dict[str, Any]] = []
        checked_fields: List[str] = []

        now = datetime.now(timezone.utc)

        for field_name, value in temporal_fields.items():
            checked_fields.append(field_name)
            parsed_dt, parse_err = self._parse_datetime(value)

            if parsed_dt is None:
                violations.append({
                    "field": field_name,
                    "value": value,
                    "issue": f"Malformed timestamp/date format: {parse_err}",
                })
                continue

            # Stale timestamp check (if configured)
            if self.config.max_timestamp_age_seconds is not None:
                # If parsed_dt has no tz, assume UTC
                dt_utc = parsed_dt if parsed_dt.tzinfo else parsed_dt.replace(tzinfo=timezone.utc)
                age_seconds = (now - dt_utc).total_seconds()
                if age_seconds > self.config.max_timestamp_age_seconds:
                    violations.append({
                        "field": field_name,
                        "value": value,
                        "issue": f"Timestamp is stale (age {age_seconds:.1f}s > allowed {self.config.max_timestamp_age_seconds}s)",
                    })

        if violations:
            issues = [f"'{v['field']}': {v['issue']}" for v in violations]
            return CheckResult(
                checker_name=self.name,
                status=CheckerStatus.INVALID,
                reason="Temporal validation failed: " + "; ".join(issues),
                details={
                    "tool_name": tool_name,
                    "violations": violations,
                    "checked_fields": checked_fields,
                },
            )

        return CheckResult(
            checker_name=self.name,
            status=CheckerStatus.VALID,
            reason=f"All {len(checked_fields)} temporal field(s) validated successfully",
            details={
                "tool_name": tool_name,
                "checked_fields": checked_fields,
            },
        )

    def _find_temporal_fields(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Identify fields that represent dates or timestamps."""
        found = {}
        for key, val in result.items():
            for pat in TEMPORAL_FIELD_PATTERNS:
                if re.match(pat, key, re.IGNORECASE):
                    # Exclude boolean or pure float metrics like 'time_elapsed_ms' if not a timestamp
                    if isinstance(val, (str, int, float)) and not isinstance(val, bool):
                        found[key] = val
                    break
        return found

    def _parse_datetime(self, value: Any) -> Tuple[Optional[datetime], str]:
        """Attempt to parse value into datetime. Supports numeric epoch and strings."""
        if isinstance(value, (int, float)):
            # Epoch timestamp in seconds or milliseconds
            try:
                # If epoch > 1e11 it's likely milliseconds
                ts = value / 1000.0 if value > 1e11 else float(value)
                return datetime.fromtimestamp(ts, tz=timezone.utc), ""
            except (OverflowError, OSError, ValueError) as e:
                return None, f"Invalid epoch numeric timestamp: {e}"

        if isinstance(value, str):
            val_clean = value.strip()
            # Try ISO formats
            for fmt in ISO_FORMATS:
                try:
                    return datetime.strptime(val_clean, fmt), ""
                except ValueError:
                    pass
            # Try fromisoformat (Python 3.11+)
            try:
                # Handle trailing Z
                if val_clean.endswith("Z"):
                    val_clean = val_clean[:-1] + "+00:00"
                return datetime.fromisoformat(val_clean), ""
            except ValueError:
                pass

            return None, f"Could not parse '{value}' using standard ISO-8601/date formats"

        return None, f"Unsupported timestamp type {type(value).__name__}"
