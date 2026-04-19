#!/usr/bin/env python3
"""Tests for get_next_task.py"""

import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from get_next_task import parse_tasks, parse_completed_from_log, resolve_next_task

DESIGN = textwrap.dedent("""\
    | Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | `TSK-001` | `Data-Agent` | EDA | `REQ-DATA-01` | None | Pending |
    | `TSK-002` | `Data-Agent` | DataLoader | `REQ-DATA-01` | `TSK-001` | Pending |
    | `TSK-003` | `Model-Agent` | Train model | `REQ-SYS-01` | `TSK-002` | Pending |
    | `TSK-004` | `MLOps-Agent` | Deploy API | `REQ-PERF-01` | `TSK-003` | Pending |
""")

LOG_NONE = ""
LOG_TSK001 = "### Task Execution: TSK-001\n* Status: Merged to main"
LOG_TSK001_AND_002 = "### Task Execution: TSK-001\n### Task Execution: TSK-002"


class TestParseDesign(unittest.TestCase):
    def test_parses_all_tasks(self):
        tasks = parse_tasks(DESIGN)
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0].task_id, "TSK-001")

    def test_parses_dependencies(self):
        tasks = parse_tasks(DESIGN)
        self.assertEqual(tasks[1].dependencies, ["TSK-001"])
        self.assertEqual(tasks[0].dependencies, [])

    def test_parses_agent(self):
        tasks = parse_tasks(DESIGN)
        self.assertEqual(tasks[0].agent, "Data-Agent")
        self.assertEqual(tasks[2].agent, "Model-Agent")


class TestParseLog(unittest.TestCase):
    def test_empty_log(self):
        self.assertEqual(parse_completed_from_log(LOG_NONE), set())

    def test_single_completed(self):
        completed = parse_completed_from_log(LOG_TSK001)
        self.assertIn("TSK-001", completed)

    def test_multiple_completed(self):
        completed = parse_completed_from_log(LOG_TSK001_AND_002)
        self.assertIn("TSK-001", completed)
        self.assertIn("TSK-002", completed)


class TestResolveNextTask(unittest.TestCase):
    def setUp(self):
        self.tasks = parse_tasks(DESIGN)

    def test_first_task_when_nothing_done(self):
        task, reason = resolve_next_task(self.tasks, set())
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "TSK-001")

    def test_second_task_after_first_done(self):
        task, _ = resolve_next_task(self.tasks, {"TSK-001"})
        self.assertEqual(task.task_id, "TSK-002")

    def test_blocked_task_not_returned(self):
        # TSK-002 blocked because TSK-001 not done
        task, _ = resolve_next_task(self.tasks, set())
        self.assertNotEqual(task.task_id, "TSK-002")

    def test_all_complete_returns_none(self):
        task, reason = resolve_next_task(self.tasks, {"TSK-001", "TSK-002", "TSK-003", "TSK-004"})
        self.assertIsNone(task)
        self.assertIn("complete", reason.lower())

    def test_specific_task_valid(self):
        task, reason = resolve_next_task(self.tasks, set(), requested_id="TSK-001")
        self.assertIsNotNone(task)
        self.assertEqual(task.task_id, "TSK-001")

    def test_specific_task_blocked(self):
        task, reason = resolve_next_task(self.tasks, set(), requested_id="TSK-002")
        self.assertIsNone(task)
        self.assertIn("TSK-001", reason)

    def test_specific_task_already_done(self):
        task, reason = resolve_next_task(self.tasks, {"TSK-001"}, requested_id="TSK-001")
        self.assertIsNone(task)
        self.assertIn("already completed", reason.lower())

    def test_nonexistent_task_id(self):
        task, reason = resolve_next_task(self.tasks, set(), requested_id="TSK-999")
        self.assertIsNone(task)
        self.assertIn("not found", reason.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
