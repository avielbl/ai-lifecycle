#!/usr/bin/env python3
"""Tests for validate_prd.py"""

import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from validate_prd import validate, ValidationResult

# ── Fixtures ───────────────────────────────────────────────────────────────────

VALID_PRD = textwrap.dedent("""\
    # Project: Fruit Defect Classifier

    ### A. Project Overview
    * **Description:** Detect defective fruit on a production line.
    * **Target Domain:** Industrial visual quality inspection

    ### B. Traceable Requirements

    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | Model deployable as REST API | Passes load test at 20 req/s |
    | `REQ-DATA-01` | Data | Balanced dataset with quality annotation | < 2% label noise verified by EDA |
    | `REQ-PERF-01` | Performance | F1-Score on defective class | >= 0.92 |

    ### C. Clarification & Decision Log
    * **Q1:** What latency? -> **User Decision:** < 50ms

    ### D. Status
    * [x] Approved for Architecture Design
""")

MISSING_SECTIONS_PRD = textwrap.dedent("""\
    # Project

    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | Some system req | Some criteria |
    | `REQ-DATA-01` | Data | Some data req | Some criteria |
    | `REQ-PERF-01` | Performance | Some perf req | Some criteria |

    * [x] Approved for Architecture Design
""")

EMPTY_ACCEPTANCE_PRD = textwrap.dedent("""\
    ### A. Project Overview
    * **Description:** Test project
    * **Target Domain:** Test

    ### B. Traceable Requirements
    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | Some req | [Criteria] |
    | `REQ-DATA-01` | Data | Some req | Good criteria |
    | `REQ-PERF-01` | Performance | Some req | Some metric >= X |

    ### D. Status
    * [x] Approved for Architecture Design
""")

MISSING_CATEGORY_PRD = textwrap.dedent("""\
    ### A. Project Overview
    * **Description:** Test

    ### B. Traceable Requirements
    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | Some req | Some criteria |
    | `REQ-SYS-02` | System | Another req | More criteria |

    ### D. Status
    * [x] Approved for Architecture Design
""")

NOT_APPROVED_PRD = textwrap.dedent("""\
    ### A. Project Overview
    * **Description:** Test

    ### B. Traceable Requirements
    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | Some req | Some criteria |
    | `REQ-DATA-01` | Data | Some req | Some criteria |
    | `REQ-PERF-01` | Performance | Some req | Some criteria |

    ### D. Status
    * [ ] Approved for Architecture Design
""")

DUPLICATE_IDS_PRD = textwrap.dedent("""\
    ### A. Project Overview
    * **Description:** Test

    ### B. Traceable Requirements
    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | Some req | Some criteria |
    | `REQ-SYS-01` | System | Duplicate | Some criteria |
    | `REQ-DATA-01` | Data | Some req | Some criteria |
    | `REQ-PERF-01` | Performance | Some req | Some criteria |

    ### D. Status
    * [x] Approved for Architecture Design
""")


# ── Test helpers ───────────────────────────────────────────────────────────────

def validate_text(text: str, tmp_path: Path) -> ValidationResult:
    p = tmp_path / "01_PRD.md"
    p.write_text(text)
    return validate(p)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestValidPRD(unittest.TestCase):
    def test_valid_prd_passes(self, tmp_path=Path("/tmp/test_valid")):
        tmp_path.mkdir(exist_ok=True)
        result = validate_text(VALID_PRD, tmp_path)
        self.assertTrue(result.passed, f"Expected PASS but got errors: {result.errors}")
        self.assertEqual(result.errors, [])


class TestMissingSections(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("/tmp/test_sections")
        self.tmp.mkdir(exist_ok=True)

    def test_missing_project_overview(self):
        result = validate_text(MISSING_SECTIONS_PRD, self.tmp)
        errors_text = " ".join(result.errors)
        self.assertIn("Project Overview", errors_text)

    def test_missing_status(self):
        prd = MISSING_SECTIONS_PRD.replace("* [x] Approved for Architecture Design", "")
        result = validate_text(prd, self.tmp)
        has_status_error = any("Status" in e or "approval" in e.lower() for e in result.errors)
        self.assertTrue(has_status_error)


class TestRequirementsTable(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("/tmp/test_reqs")
        self.tmp.mkdir(exist_ok=True)

    def test_empty_acceptance_criteria_fails(self):
        result = validate_text(EMPTY_ACCEPTANCE_PRD, self.tmp)
        self.assertFalse(result.passed)
        self.assertTrue(any("Acceptance Criteria" in e for e in result.errors))

    def test_missing_category_fails(self):
        result = validate_text(MISSING_CATEGORY_PRD, self.tmp)
        self.assertFalse(result.passed)
        errors_text = " ".join(result.errors)
        self.assertIn("REQ-DATA", errors_text)
        self.assertIn("REQ-PERF", errors_text)

    def test_duplicate_req_ids_fails(self):
        result = validate_text(DUPLICATE_IDS_PRD, self.tmp)
        self.assertFalse(result.passed)
        self.assertTrue(any("Duplicate" in e for e in result.errors))


class TestApprovalStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = Path("/tmp/test_approval")
        self.tmp.mkdir(exist_ok=True)

    def test_not_approved_fails(self):
        result = validate_text(NOT_APPROVED_PRD, self.tmp)
        self.assertFalse(result.passed)
        self.assertTrue(any("approval" in e.lower() or "approved" in e.lower()
                            for e in result.errors))


class TestFileNotFound(unittest.TestCase):
    def test_missing_file(self):
        result = validate(Path("/nonexistent/path/01_PRD.md"))
        self.assertFalse(result.passed)
        self.assertTrue(any("not found" in e.lower() for e in result.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
