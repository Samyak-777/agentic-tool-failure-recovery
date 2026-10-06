"""
Unit Tests for Layer 2 (Structured Failure Diagnosis) and Layer 3 (Tool Memory & Recovery Controller).
"""

import unittest
from diagnosis.taxonomy import (
    FailureCategory,
    PersistenceType,
    RecoveryDirective,
    StructuredDiagnosis
)
from diagnosis.engine import StructuredDiagnosisEngine
from tool_memory.registry import ToolHealthRegistry, ToolHealthStatus
from tool_memory.memory import ToolMemory
from tool_memory.budget import BudgetTracker, BudgetConfig
from tool_memory.recovery_controller import RecoveryController

class TestLayer2DiagnosisEngine(unittest.TestCase):
    def setUp(self):
        self.engine = StructuredDiagnosisEngine(max_transient_retries=2)

    def test_clean_execution_diagnosis(self):
        raw_result = {"status": "success", "price": 150}
        diag = self.engine.diagnose("get_stock", {"symbol": "AAPL"}, raw_result)
        self.assertTrue(diag.is_valid)
        self.assertEqual(diag.recommended_action, RecoveryDirective.CONTINUE)

    def test_http_404_permanent_diagnosis(self):
        raw_result = {"error": "HTTP 404: Not Found"}
        diag = self.engine.diagnose("search_flights", {"from": "NYC"}, raw_result)
        self.assertFalse(diag.is_valid)
        self.assertEqual(diag.persistence, PersistenceType.PERMANENT)
        self.assertEqual(diag.recommended_action, RecoveryDirective.REROUTE)

    def test_http_429_transient_diagnosis(self):
        raw_result = {"error": "HTTP 429: Rate Limit Exceeded"}
        diag = self.engine.diagnose("get_weather", {"city": "Tokyo"}, raw_result, tool_call_history=[])
        self.assertFalse(diag.is_valid)
        self.assertEqual(diag.persistence, PersistenceType.TRANSIENT)
        self.assertEqual(diag.recommended_action, RecoveryDirective.RETRY)

    def test_sov_range_violation_diagnosis(self):
        val_result = {
            "pipeline_status": "INVALID",
            "violations": [{"checker_name": "range_checker", "message": "Price -50 is negative"}]
        }
        diag = self.engine.diagnose("get_stock", {"symbol": "TSLA"}, {"price": -50}, validation_result=val_result)
        self.assertFalse(diag.is_valid)
        self.assertEqual(diag.category, FailureCategory.SEMANTIC_RANGE_ERROR)
        self.assertEqual(diag.persistence, PersistenceType.TRANSIENT)
        self.assertEqual(diag.recommended_action, RecoveryDirective.RETRY)


class TestLayer3ToolMemoryAndController(unittest.TestCase):
    def setUp(self):
        self.registry = ToolHealthRegistry(failure_threshold_to_blacklist=2)
        self.memory = ToolMemory()
        self.budget = BudgetTracker(BudgetConfig(max_total_tool_calls=5, max_recovery_attempts=3, max_retries_per_tool=2))
        self.alt_map = {"get_stock_alpha": ["get_stock_finnhub", "get_stock_yahoo"]}
        self.controller = RecoveryController(
            health_registry=self.registry,
            memory=self.memory,
            budget_tracker=self.budget,
            alternative_tools_map=self.alt_map
        )

    def test_retry_on_transient_within_budget(self):
        diag = StructuredDiagnosis(
            tool_name="get_stock_alpha",
            is_valid=False,
            category=FailureCategory.EXTERNAL_SERVICE_ERROR,
            persistence=PersistenceType.TRANSIENT,
            root_cause="Rate limit hit",
            severity="MEDIUM",
            recommended_action=RecoveryDirective.RETRY
        )
        decision = self.controller.decide_recovery(diag, {"symbol": "AAPL"}, step_num=1)
        self.assertEqual(decision["action"], "retry")
        self.assertEqual(decision["suggested_tool"], "get_stock_alpha")

    def test_reroute_when_tool_blacklisted(self):
        # Fail twice to blacklist
        self.registry.record_failure("get_stock_alpha", "network", is_permanent=False)
        self.registry.record_failure("get_stock_alpha", "network", is_permanent=False)
        self.assertTrue(self.registry.is_blacklisted("get_stock_alpha"))

        diag = StructuredDiagnosis(
            tool_name="get_stock_alpha",
            is_valid=False,
            category=FailureCategory.EXTERNAL_SERVICE_ERROR,
            persistence=PersistenceType.PERMANENT,
            root_cause="Persistent failure",
            severity="HIGH",
            recommended_action=RecoveryDirective.REROUTE
        )
        decision = self.controller.decide_recovery(diag, {"symbol": "AAPL"}, step_num=3)
        self.assertEqual(decision["action"], "reroute")
        self.assertEqual(decision["suggested_tool"], "get_stock_finnhub")

    def test_abort_when_budget_exhausted(self):
        # Exhaust recovery attempts
        self.budget.recovery_attempts = 3
        diag = StructuredDiagnosis(
            tool_name="get_stock_alpha",
            is_valid=False,
            category=FailureCategory.EXTERNAL_SERVICE_ERROR,
            persistence=PersistenceType.TRANSIENT,
            root_cause="Rate limit",
            severity="MEDIUM",
            recommended_action=RecoveryDirective.RETRY
        )
        decision = self.controller.decide_recovery(diag, {"symbol": "AAPL"}, step_num=4)
        self.assertEqual(decision["action"], "abort")

if __name__ == "__main__":
    unittest.main()
