#!/usr/bin/env python3
"""Tests for baseline_classifier.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from baseline_classifier import (
    load_csv, _to_numeric_matrix,
    parse_perf_requirements, _evaluate, _guess_metric,
    generate_report, ModelResult,
)

# If sklearn/numpy unavailable, skip integration tests
try:
    import numpy as np
    import sklearn
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

TMP = Path("/tmp/test_baseline")
TMP.mkdir(exist_ok=True)


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.write_text(content)
    return p


CSV_BALANCED = (
    "feature1,feature2,label\n"
    "1.0,2.0,cat\n"
    "1.1,2.1,cat\n"
    "3.0,4.0,dog\n"
    "3.1,4.1,dog\n"
    "5.0,6.0,cat\n"
    "5.1,6.1,dog\n"
)

PRD_TEXT = (
    "### B. Traceable Requirements\n"
    "| Requirement ID | Category | Description | Acceptance Criteria |\n"
    "| :--- | :--- | :--- | :--- |\n"
    "| `REQ-PERF-01` | Performance | F1 Score | >= 0.80 |\n"
    "| `REQ-PERF-02` | Performance | Accuracy | >= 0.75 |\n"
)


class TestCSVLoading(unittest.TestCase):
    def test_loads_features_and_labels(self):
        p = write("data.csv", CSV_BALANCED)
        feature_names, X_raw, y_raw = load_csv(p, None)
        self.assertIn("feature1", feature_names)
        self.assertIn("feature2", feature_names)
        self.assertNotIn("label", feature_names)
        self.assertEqual(len(y_raw), 6)

    def test_explicit_label_col(self):
        csv = "x,y,class\n1,2,a\n3,4,b\n"
        p = write("explicit.csv", csv)
        feature_names, X_raw, y_raw = load_csv(p, "class")
        self.assertNotIn("class", feature_names)
        self.assertEqual(y_raw[0], "a")

    def test_missing_label_raises(self):
        p = write("nolabel.csv", "a,b\n1,2\n3,4\n")
        with self.assertRaises(ValueError):
            load_csv(p, None)

    def test_no_standard_label_col_raises(self):
        # No standard label column name and no explicit label_col specified
        p = write("no_std_label.csv", "feature_a,feature_b\n1.0,2.0\n3.0,4.0\n")
        with self.assertRaises(ValueError):
            load_csv(p, None)


class TestPRDParsing(unittest.TestCase):
    def test_parses_perf_reqs(self):
        p = write("prd.md", PRD_TEXT)
        reqs = parse_perf_requirements(p)
        self.assertEqual(len(reqs), 2)
        self.assertEqual(reqs[0].req_id, "REQ-PERF-01")

    def test_f1_keyword(self):
        p = write("prd.md", PRD_TEXT)
        reqs = parse_perf_requirements(p)
        self.assertEqual(reqs[0].metric_keyword, "f1")

    def test_accuracy_keyword(self):
        p = write("prd.md", PRD_TEXT)
        reqs = parse_perf_requirements(p)
        self.assertEqual(reqs[1].metric_keyword, "accuracy")

    def test_missing_file_returns_empty(self):
        reqs = parse_perf_requirements(Path("/nonexistent.md"))
        self.assertEqual(reqs, [])


class TestEvaluation(unittest.TestCase):
    def test_pass_gte(self):
        self.assertEqual(_evaluate(">= 0.80", 0.85), "PASS")
        self.assertEqual(_evaluate(">= 0.80", 0.79), "FAIL")

    def test_pass_lt(self):
        self.assertEqual(_evaluate("< 50", 40.0), "PASS")
        self.assertEqual(_evaluate("< 50", 60.0), "FAIL")

    def test_unknown_criteria(self):
        self.assertEqual(_evaluate("very good accuracy", 0.9), "UNKNOWN")


class TestMetricKeyword(unittest.TestCase):
    def test_f1_detection(self):
        self.assertEqual(_guess_metric("F1-Score >= 0.92"), "f1")

    def test_accuracy_detection(self):
        self.assertEqual(_guess_metric("accuracy >= 0.90"), "accuracy")

    def test_precision_detection(self):
        self.assertEqual(_guess_metric("precision on defects"), "precision")

    def test_unknown(self):
        self.assertIsNone(_guess_metric("response time under 100ms"))


class TestReportGeneration(unittest.TestCase):
    def _make_result(self):
        r = ModelResult(
            name="Random Forest",
            cv_mean=0.91, cv_std=0.02,
            test_accuracy=0.93, test_f1=0.92,
            test_precision=0.91, test_recall=0.93,
            roc_auc=0.97,
            best_params={"classifier__n_estimators": 200},
            feature_importances=[("feature1", 0.6), ("feature2", 0.4)],
            confusion=[[3, 1], [0, 4]],
            classification_report_str="              precision    recall  f1-score\ncat       0.91      0.93      0.92",
        )
        return r

    def test_report_contains_model_name(self):
        r = self._make_result()
        report = generate_report([r], ["feature1", "feature2"], ["cat", "dog"],
                                 Path("data.csv"), [], 8)
        self.assertIn("Random Forest", report)

    def test_report_has_sections(self):
        r = self._make_result()
        report = generate_report([r], ["feature1", "feature2"], ["cat", "dog"],
                                 Path("data.csv"), [], 8)
        self.assertIn("## A. Model Comparison", report)
        self.assertIn("## B. Top Feature Importances", report)
        self.assertIn("## C. Confusion Matrix", report)

    def test_report_shows_prd_status(self):
        import textwrap
        p = write("prd.md", PRD_TEXT)
        reqs = parse_perf_requirements(p)
        r = self._make_result()
        report = generate_report([r], ["feature1", "feature2"], ["cat", "dog"],
                                 Path("data.csv"), reqs, 8)
        self.assertIn("## E. PRD Requirement Status", report)

    def test_ranking_best_first(self):
        r1 = ModelResult("ModelA", 0.9, 0.01, 0.9, 0.9, 0.9, 0.9)
        r2 = ModelResult("ModelB", 0.8, 0.01, 0.8, 0.75, 0.8, 0.8)
        report = generate_report([r1, r2], [], ["a", "b"], Path("d.csv"), [], 10)
        pos_a = report.find("ModelA")
        pos_b = report.find("ModelB")
        self.assertLess(pos_a, pos_b)


@unittest.skipUnless(HAS_DEPS, "sklearn/numpy not installed")
class TestNumericMatrix(unittest.TestCase):
    def test_converts_numeric_columns(self):
        p = write("data.csv", CSV_BALANCED)
        feature_names, X_raw, y_raw = load_csv(p, None)
        X, numeric_names = _to_numeric_matrix(X_raw, feature_names)
        self.assertEqual(X.shape[0], 6)
        self.assertEqual(X.shape[1], 2)
        self.assertIn("feature1", numeric_names)

    def test_skips_non_numeric(self):
        csv = "num,text,label\n1.0,hello,a\n2.0,world,b\n3.0,foo,a\n"
        p = write("mixed.csv", csv)
        feature_names, X_raw, _ = load_csv(p, None)
        X, names = _to_numeric_matrix(X_raw, feature_names)
        self.assertEqual(X.shape[1], 1)
        self.assertNotIn("text", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
