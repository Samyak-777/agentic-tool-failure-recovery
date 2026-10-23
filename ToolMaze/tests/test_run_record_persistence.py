
import json
import tempfile
import unittest
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.telemetry.recorder import (
    TelemetryManager,
    TelemetryRecorder,
)


class TestRunRecordPersistence(unittest.TestCase):
    def test_task_jsons_survive_run_finalization(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            records_root = Path(temp_dir)

            task_definitions = [
                {
                    "task_id": "C1_task_001",
                    "complexity": "C1",
                    "perturbation_mode": "P0",
                    "task_description": "Persistence test task 1",
                },
                {
                    "task_id": "C1_task_002",
                    "complexity": "C1",
                    "perturbation_mode": "P1",
                    "task_description": "Persistence test task 2",
                },
                {
                    "task_id": "C1_task_003",
                    "complexity": "C1",
                    "perturbation_mode": "P2",
                    "task_description": "Persistence test task 3",
                },
            ]

            for agent_type in ("care", "baseline"):
                run_id = f"test_{agent_type}"

                manager = TelemetryManager(
                    run_id=run_id,
                    agent_type=agent_type,
                    model="test-model",
                    category="c1",
                    config={},
                    base_dir=records_root,
                )

                expected_files = []

                for task in task_definitions:
                    recorder = TelemetryRecorder(
                        manager,
                        task,
                        agent_type=agent_type,
                    )

                    recorder.complete_task(
                        passed=True,
                        judgement={"pass": True},
                        token_usage={"total_tokens": 10},
                    )

                    expected_files.append(
                        manager.task_records_dir
                        / f"{task['task_id']}_"
                        f"{task['perturbation_mode']}.json"
                    )

                manager.finalize_run()

                # Records must still exist AFTER finalization.
                for task, record_file in zip(
                    task_definitions, expected_files
                ):
                    self.assertTrue(
                        record_file.is_file(),
                        f"Missing persistent record: {record_file}",
                    )

                    with record_file.open(
                        "r", encoding="utf-8"
                    ) as file:
                        record = json.load(file)

                    self.assertEqual(record["run_id"], run_id)
                    self.assertEqual(
                        record["agent_type"], agent_type
                    )
                    self.assertEqual(
                        record["task_id"], task["task_id"]
                    )
                    self.assertEqual(
                        record["mode"], task["perturbation_mode"]
                    )
                    self.assertEqual(
                        record["task_definition"], task
                    )

                self.assertTrue(
                    (manager.records_dir / "run_manifest.json").is_file()
                )
                self.assertTrue(
                    (manager.records_dir / "run_summary.json").is_file()
                )

                # All three task records should be present.
                self.assertEqual(
                    len(list(manager.task_records_dir.glob("*.json"))),
                    3,
                )


if __name__ == "__main__":
    unittest.main()
