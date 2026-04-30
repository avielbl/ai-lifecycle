#!/usr/bin/env python3
"""Tests for check_req_coverage.py"""

import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from check_req_coverage import check_coverage, CoverageResult

TMP = Path("/tmp/test_coverage")
TMP.mkdir(exist_ok=True)

PRD = textwrap.dedent("""\
    ### B. Traceable Requirements
    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | REST API | Load test pass |
    | `REQ-DATA-01` | Data | Clean dataset | < 2% noise |
    | `REQ-PERF-01` | Performance | F1 score | >= 0.92 |
""")

ARCH_FULL_COVERAGE = textwrap.dedent("""\
    ### B. Component Design & Traceability
    | Component | Description | Tech Stack | Satisfies Requirement |
    | :--- | :--- | :--- | :--- |
    | Data Profiling | EDA | pandas | `REQ-DATA-01` |
    | Training Core | ResNet-18 | PyTorch | `REQ-SYS-01` |
    | Serving API | FastAPI | FastAPI+ONNX | `REQ-PERF-01` |
""")

ARCH_MISSING_PERF = textwrap.dedent("""\
    ### B. Component Design & Traceability
    | Component | Description | Tech Stack | Satisfies Requirement |
    | :--- | :--- | :--- | :--- |
    | Data Profiling | EDA | pandas | `REQ-DATA-01` |
    | Training Core | ResNet-18 | PyTorch | `REQ-SYS-01` |
""")

ARCH_WITH_PHANTOM = textwrap.dedent("""\
    ### B. Component Design & Traceability
    | Component | Description | Tech Stack | Satisfies Requirement |
    | :--- | :--- | :--- | :--- |
    | Data Profiling | EDA | pandas | `REQ-DATA-01` |
    | Training Core | ResNet-18 | PyTorch | `REQ-SYS-01` |
    | Serving API | FastAPI | FastAPI | `REQ-PERF-01` |
    | Ghost Component | Unknown | Unknown | `REQ-GHOST-99` |
""")


def write_files(prd_text: str, arch_text: str) -> tuple[Path, Path]:
    prd = TMP / "01_PRD.md"
    arch = TMP / "02_Architecture.md"
    prd.write_text(prd_text)
    arch.write_text(arch_text)
    return prd, arch


class TestFullCoverage(unittest.TestCase):
    def test_passes_when_all_reqs_covered(self):
        prd, arch = write_files(PRD, ARCH_FULL_COVERAGE)
        result = check_coverage(prd, arch)
        self.assertTrue(result.passed)
        self.assertEqual(result.uncovered, set())


class TestMissingCoverage(unittest.TestCase):
    def test_fails_when_req_not_in_arch(self):
        prd, arch = write_files(PRD, ARCH_MISSING_PERF)
        result = check_coverage(prd, arch)
        self.assertFalse(result.passed)
        self.assertIn("REQ-PERF-01", result.uncovered)

    def test_covered_reqs_not_reported(self):
        prd, arch = write_files(PRD, ARCH_MISSING_PERF)
        result = check_coverage(prd, arch)
        self.assertNotIn("REQ-SYS-01", result.uncovered)
        self.assertNotIn("REQ-DATA-01", result.uncovered)


class TestPhantomIds(unittest.TestCase):
    def test_phantom_ids_detected(self):
        prd, arch = write_files(PRD, ARCH_WITH_PHANTOM)
        result = check_coverage(prd, arch)
        self.assertIn("REQ-GHOST-99", result.phantom)

    def test_phantom_does_not_cause_failure(self):
        prd, arch = write_files(PRD, ARCH_WITH_PHANTOM)
        result = check_coverage(prd, arch)
        # phantom IDs are warnings, not failures
        self.assertTrue(result.passed)


class TestMissingFiles(unittest.TestCase):
    def test_missing_prd(self):
        result = check_coverage(Path("/no/prd.md"), TMP / "02_Architecture.md")
        self.assertFalse(result.passed)
        self.assertTrue(any("PRD" in e for e in result.errors))

    def test_missing_arch(self):
        prd = TMP / "01_PRD.md"
        prd.write_text(PRD)
        result = check_coverage(prd, Path("/no/arch.md"))
        self.assertFalse(result.passed)
        self.assertTrue(any("Architecture" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
