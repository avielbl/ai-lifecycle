#!/usr/bin/env python3
"""Tests for validate_design.py"""

import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from validate_design import validate

TMP = Path("/tmp/test_design")
TMP.mkdir(exist_ok=True)

VALID_DESIGN = textwrap.dedent("""\
    ### A. Sub-Agent Task Allocation
    | Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | `TSK-001` | `Data-Agent` | Execute EDA: analyze class distributions, annotation quality, verify splits | `REQ-DATA-01` | None | Pending |
    | `TSK-002` | `Data-Agent` | Implement DataLoader with augmentation | `REQ-DATA-01` | `TSK-001` | Pending |
    | `TSK-003` | `Model-Agent` | Train ResNet-18 with Focal Loss | `REQ-SYS-01` | `TSK-002` | Pending |
    | `TSK-004` | `MLOps-Agent` | Deploy FastAPI serving endpoint | `REQ-PERF-01` | `TSK-003` | Pending |
""")

MISSING_TSK001 = textwrap.dedent("""\
    ### A. Sub-Agent Task Allocation
    | Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | `TSK-002` | `Data-Agent` | Implement DataLoader | `REQ-DATA-01` | None | Pending |
    | `TSK-003` | `Model-Agent` | Train model | `REQ-SYS-01` | `TSK-002` | Pending |
""")

WRONG_AGENT_TSK001 = textwrap.dedent("""\
    ### A. Sub-Agent Task Allocation
    | Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | `TSK-001` | `Model-Agent` | Run EDA | `REQ-DATA-01` | None | Pending |
    | `TSK-002` | `Data-Agent` | Implement DataLoader | `REQ-DATA-01` | `TSK-001` | Pending |
""")

MISSING_REQ = textwrap.dedent("""\
    ### A. Sub-Agent Task Allocation
    | Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | `TSK-001` | `Data-Agent` | EDA | `REQ-DATA-01` | None | Pending |
    | `TSK-002` | `Model-Agent` | Train model | - | `TSK-001` | Pending |
""")

BAD_DEPENDENCY = textwrap.dedent("""\
    ### A. Sub-Agent Task Allocation
    | Task ID | Assigned Agent | Task Description | Linked Requirement | Dependencies | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | `TSK-001` | `Data-Agent` | EDA | `REQ-DATA-01` | None | Pending |
    | `TSK-002` | `Model-Agent` | Train model | `REQ-SYS-01` | `TSK-099` | Pending |
""")


def design_file(text: str) -> Path:
    p = TMP / "03_Detailed_Design.md"
    p.write_text(text)
    return p


class TestValidDesign(unittest.TestCase):
    def test_valid_design_passes(self):
        result = validate(design_file(VALID_DESIGN))
        self.assertTrue(result.passed, f"Errors: {result.errors}")

    def test_task_count(self):
        result = validate(design_file(VALID_DESIGN))
        self.assertEqual(len(result.tasks), 4)


class TestTsk001(unittest.TestCase):
    def test_missing_tsk001_fails(self):
        result = validate(design_file(MISSING_TSK001))
        self.assertFalse(result.passed)
        self.assertTrue(any("TSK-001" in e for e in result.errors))

    def test_wrong_agent_tsk001_fails(self):
        result = validate(design_file(WRONG_AGENT_TSK001))
        self.assertFalse(result.passed)
        self.assertTrue(any("Data-Agent" in e for e in result.errors))


class TestLinkedRequirements(unittest.TestCase):
    def test_missing_linked_req_fails(self):
        result = validate(design_file(MISSING_REQ))
        self.assertFalse(result.passed)
        self.assertTrue(any("TSK-002" in e for e in result.errors))


class TestDependencies(unittest.TestCase):
    def test_bad_dependency_fails(self):
        result = validate(design_file(BAD_DEPENDENCY))
        self.assertFalse(result.passed)
        self.assertTrue(any("TSK-099" in e for e in result.errors))


class TestFileNotFound(unittest.TestCase):
    def test_missing_file(self):
        result = validate(Path("/no/such/file.md"))
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
