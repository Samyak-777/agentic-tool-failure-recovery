"""Standalone test runner without requiring pytest dependency."""

import os
import sys
from pathlib import Path

# Ensure ToolMaze is on sys.path
toolmaze_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(toolmaze_root))

from semantic_validation.tests import (
    test_schema_checker,
    test_type_checker,
    test_required_checker,
    test_range_checker,
    test_temporal_checker,
    test_entity_checker,
    test_cross_field_checker,
    test_state_checker,
    test_pipeline,
    test_metrics,
)
from semantic_validation.tests.fixtures.mock_outputs import MockToolLoader
from semantic_validation.schema.extractor import SchemaExtractor
from semantic_validation.schema.range_registry import RangeRegistry


def run_all_tests():
    modules = [
        ("test_schema_checker", test_schema_checker),
        ("test_type_checker", test_type_checker),
        ("test_required_checker", test_required_checker),
        ("test_range_checker", test_range_checker),
        ("test_temporal_checker", test_temporal_checker),
        ("test_entity_checker", test_entity_checker),
        ("test_cross_field_checker", test_cross_field_checker),
        ("test_state_checker", test_state_checker),
        ("test_pipeline", test_pipeline),
        ("test_metrics", test_metrics),
    ]

    passed = 0
    failed = 0
    errors = []

    print("=" * 60)
    print("Running SVL Test Suite")
    print("=" * 60)

    for mod_name, mod in modules:
        for attr in dir(mod):
            if attr.startswith("test_") and callable(getattr(mod, attr)):
                fn = getattr(mod, attr)
                # Check parameters for fixtures
                import inspect
                sig = inspect.signature(fn)
                kwargs = {}
                for param in sig.parameters:
                    if param == "checker":
                        if "schema" in mod_name:
                            loader = MockToolLoader()
                            extractor = SchemaExtractor(loader)
                            from semantic_validation.checkers.schema_checker import SchemaChecker
                            kwargs["checker"] = SchemaChecker(extractor)
                        elif "type" in mod_name:
                            loader = MockToolLoader()
                            extractor = SchemaExtractor(loader)
                            from semantic_validation.checkers.type_checker import TypeChecker
                            kwargs["checker"] = TypeChecker(extractor)
                        elif "required" in mod_name:
                            loader = MockToolLoader()
                            extractor = SchemaExtractor(loader)
                            from semantic_validation.checkers.required_checker import RequiredFieldChecker
                            kwargs["checker"] = RequiredFieldChecker(extractor)
                        elif "range" in mod_name:
                            from semantic_validation.checkers.range_checker import RangeChecker
                            kwargs["checker"] = RangeChecker(RangeRegistry())
                        elif "cross_field" in mod_name:
                            from semantic_validation.checkers.cross_field_checker import CrossFieldChecker
                            kwargs["checker"] = CrossFieldChecker()

                try:
                    fn(**kwargs)
                    print(f"  ✓ {mod_name}::{attr}")
                    passed += 1
                except Exception as e:
                    print(f"  ✗ {mod_name}::{attr}: {e}")
                    failed += 1
                    errors.append((f"{mod_name}::{attr}", str(e)))

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    if errors:
        for name, err in errors:
            print(f"FAIL: {name} -> {err}")
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
