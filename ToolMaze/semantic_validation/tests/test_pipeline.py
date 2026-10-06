"""Integration tests for SemanticValidationPipeline."""

import pytest
from semantic_validation import (
    SemanticValidationPipeline,
    ValidationConfig,
    CheckerFlags,
    PipelineStatus,
    CheckerStatus,
)
from semantic_validation.tests.fixtures.mock_outputs import MockToolLoader


def test_pipeline_valid_run():
    config = ValidationConfig(enabled=True)
    loader = MockToolLoader()
    pipeline = SemanticValidationPipeline(config, loader)

    state = pipeline.create_execution_state("exec-1", "task-1")
    output = {"temperature_celsius": 25, "condition": "Sunny"}

    val_res = pipeline.validate(
        tool_name="get_weather_openweather",
        arguments={"city": "Tokyo"},
        result=output,
        execution_id="exec-1",
        task_id="task-1",
        step=1,
    )

    assert val_res.pipeline_status == PipelineStatus.VALID
    assert "schema" in val_res.checks
    assert val_res.checks["schema"].status == CheckerStatus.VALID
    assert len(val_res.failed_checks) == 0

    pipeline.destroy_execution_state("exec-1")


def test_pipeline_invalid_injection_payload():
    config = ValidationConfig(enabled=True)
    loader = MockToolLoader()
    pipeline = SemanticValidationPipeline(config, loader)

    pipeline.create_execution_state("exec-2", "task-2")
    # Invalid: temperature_celsius is a string "hot" instead of integer
    corrupted_output = {"temperature_celsius": "hot", "condition": "Sunny"}

    val_res = pipeline.validate(
        tool_name="get_weather_openweather",
        arguments={"city": "Tokyo"},
        result=corrupted_output,
        execution_id="exec-2",
        task_id="task-2",
        step=1,
    )

    assert val_res.pipeline_status == PipelineStatus.INVALID
    assert "type" in val_res.failed_checks

    # Verify Option A payload structure
    payload = val_res.to_agent_failure_payload(corrupted_output)
    assert payload["validation_failed"] is True
    assert payload["validation_status"] == "INVALID"
    assert "type" in payload["validation_failed_checks"]
    assert payload["untrusted_output"] == corrupted_output

    pipeline.destroy_execution_state("exec-2")


def test_pipeline_inconclusive_run():
    config = ValidationConfig(enabled=True)
    loader = MockToolLoader()
    pipeline = SemanticValidationPipeline(config, loader)

    pipeline.create_execution_state("exec-3", "task-3")
    # Tool has no schema, no range rules, no temporal, no entity match
    output = {"arbitrary_data": 42}

    val_res = pipeline.validate(
        tool_name="no_schema_tool",
        arguments={"param": 1},
        result=output,
        execution_id="exec-3",
        task_id="task-3",
        step=1,
    )

    assert val_res.pipeline_status == PipelineStatus.INCONCLUSIVE
    assert "inconclusive" in val_res.reason.lower()

    pipeline.destroy_execution_state("exec-3")
