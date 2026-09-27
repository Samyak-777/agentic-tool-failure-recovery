"""
semantic_validation/core/status.py

Defines the canonical status enumerations for the SVL.

CHECKER-LEVEL statuses (per individual checker):
    VALID           — checker ran and output is semantically valid
    INVALID         — checker ran and detected a concrete violation
    NOT_APPLICABLE  — checker cannot evaluate this tool/output combination
                      (missing schema, no applicable rule, error path, etc.)
    ERROR           — checker itself encountered an unexpected exception

PIPELINE-LEVEL statuses (aggregate over all checkers):
    VALID           — at least one checker returned VALID and none returned INVALID
    INVALID         — at least one checker returned INVALID (regardless of others)
    INCONCLUSIVE    — all checkers returned NOT_APPLICABLE or ERROR;
                      insufficient information to establish semantic validity
                      NOTE: INCONCLUSIVE != VALID. The agent receives the result
                      unchanged (no injection). Log as INCONCLUSIVE in trace.
    ERROR           — the pipeline itself failed (not a checker failure)

Research note:
    INCONCLUSIVE is a deliberate status. We must NOT conflate
    "no validator had an opinion" with "the output is valid."
    This preserves honest research claims about coverage.
"""

from enum import Enum


class CheckerStatus(str, Enum):
    """Status for an individual checker's decision."""
    VALID = "VALID"
    INVALID = "INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class PipelineStatus(str, Enum):
    """
    Aggregate status for the full validation pipeline.

    Precedence rule (highest wins):
        INVALID > ERROR > VALID > INCONCLUSIVE

    i.e.  any INVALID  → pipeline = INVALID
          no INVALID, any ERROR → pipeline = ERROR
          no INVALID, no ERROR, any VALID → pipeline = VALID
          all NOT_APPLICABLE → pipeline = INCONCLUSIVE
    """
    VALID = "VALID"
    INVALID = "INVALID"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"

    @staticmethod
    def aggregate(checker_statuses: list) -> "PipelineStatus":
        """
        Compute pipeline status from a list of CheckerStatus values.

        Args:
            checker_statuses: List of CheckerStatus values from all checkers.

        Returns:
            PipelineStatus according to precedence rule above.
        """
        statuses = set(checker_statuses)

        if CheckerStatus.INVALID in statuses:
            return PipelineStatus.INVALID

        if CheckerStatus.ERROR in statuses:
            return PipelineStatus.ERROR

        if CheckerStatus.VALID in statuses:
            return PipelineStatus.VALID

        # All checkers returned NOT_APPLICABLE (or empty)
        return PipelineStatus.INCONCLUSIVE
