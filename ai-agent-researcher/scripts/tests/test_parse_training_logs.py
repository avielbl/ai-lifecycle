#!/usr/bin/env python3
"""Tests for parse_training_logs.py"""

import csv
import json
import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from parse_training_logs import (
    parse_csv_log, parse_json_log, parse_perf_requirements,
    compare_requirements, find_best_epoch, _evaluate_against_target,
)

TMP = Path("/tmp/test_logs")
TMP.mkdir(exist_ok=True)

PRD_TEXT = textwrap.dedent("""\
    ### B. Traceable Requirements
    | Requirement ID | Category | Description | Acceptance Criteria |
    | :--- | :--- | :--- | :--- |
    | `REQ-SYS-01` | System | REST API | Passes load test |
    | `REQ-DATA-01` | Data | Clean dataset | < 2% noise |
    | `REQ-PERF-01` | Performance | F1-Score on defective class | >= 0.92 |
    | `REQ-PERF-02` | Performance | Inference latency | < 50 |
""")

CSV_LOG = (
    "epoch,train_loss,val_loss,f1,precision,recall\n"
    "0,0.85,0.90,0.71,0.75,0.68\n"
    "1,0.72,0.78,0.80,0.82,0.79\n"
    "2,0.61,0.69,0.87,0.88,0.86\n"
    "3,0.55,0.65,0.91,0.90,0.92\n"
)

JSON_LOG = json.dumps([
    {"epoch": 0, "train_loss": 0.85, "val_loss": 0.90, "f1": 0.71},
    {"epoch": 1, "train_loss": 0.72, "val_loss": 0.78, "f1": 0.80},
    {"epoch": 2, "train_loss": 0.61, "val_loss": 0.65, "f1": 0.93},
])

JSON_WRAPPED = json.dumps({"history": [
    {"epoch": 0, "val_loss": 0.90, "f1": 0.71},
    {"epoch": 1, "val_loss": 0.65, "f1": 0.93},
]})


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.write_text(content)
    return p


class TestCSVParsing(unittest.TestCase):
    def setUp(self):
        self.log = write("log.csv", CSV_LOG)

    def test_parses_epochs(self):
        epochs = parse_csv_log(self.log)
        self.assertEqual(len(epochs), 4)

    def test_parses_val_loss(self):
        epochs = parse_csv_log(self.log)
        self.assertAlmostEqual(epochs[0].val_loss, 0.90)

    def test_parses_extra_metrics(self):
        epochs = parse_csv_log(self.log)
        self.assertIn("f1", epochs[0].extra)
        self.assertAlmostEqual(epochs[3].extra["f1"], 0.91)


class TestJSONParsing(unittest.TestCase):
    def test_plain_list(self):
        log = write("log.json", JSON_LOG)
        epochs = parse_json_log(log)
        self.assertEqual(len(epochs), 3)

    def test_wrapped_history(self):
        log = write("log_wrapped.json", JSON_WRAPPED)
        epochs = parse_json_log(log)
        self.assertEqual(len(epochs), 2)


class TestBestEpoch(unittest.TestCase):
    def test_finds_min_val_loss(self):
        log = write("best.csv", CSV_LOG)
        epochs = parse_csv_log(log)
        best = find_best_epoch(epochs)
        self.assertEqual(best.epoch, 3)
        self.assertAlmostEqual(best.val_loss, 0.65)


class TestPRDParsing(unittest.TestCase):
    def test_parses_perf_reqs_only(self):
        prd = write("prd.md", PRD_TEXT)
        reqs = parse_perf_requirements(prd)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0].req_id, "REQ-PERF-01")

    def test_f1_keyword_detected(self):
        prd = write("prd.md", PRD_TEXT)
        reqs = parse_perf_requirements(prd)
        f1_req = next(r for r in reqs if r.req_id == "REQ-PERF-01")
        self.assertEqual(f1_req.metric_keyword, "f1")


class TestEvaluation(unittest.TestCase):
    def test_pass_gte(self):
        self.assertEqual(_evaluate_against_target(">= 0.92", 0.93), "PASS")
        self.assertEqual(_evaluate_against_target(">= 0.92", 0.91), "FAIL")

    def test_pass_lt(self):
        self.assertEqual(_evaluate_against_target("< 50", 43.0), "PASS")
        self.assertEqual(_evaluate_against_target("< 50", 55.0), "FAIL")

    def test_no_operator_unknown(self):
        self.assertEqual(_evaluate_against_target("good accuracy", 0.95), "UNKNOWN")


class TestComparisons(unittest.TestCase):
    def test_fail_detected(self):
        log = write("log.csv", CSV_LOG)
        prd = write("prd.md", PRD_TEXT)
        epochs = parse_csv_log(log)
        reqs = parse_perf_requirements(prd)
        comparisons = compare_requirements(reqs, epochs)
        f1_comp = next(c for c in comparisons if c.req_id == "REQ-PERF-01")
        # Best F1 in CSV is 0.91, target is >= 0.92 → FAIL
        self.assertEqual(f1_comp.status, "FAIL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
