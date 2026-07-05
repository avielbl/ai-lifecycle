#!/usr/bin/env python3
"""Tests for clustering_explorer.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from clustering_explorer import (
    load_numeric_csv, preprocess, generate_report, ClusterResult,
)

try:
    import numpy as np
    import sklearn
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

TMP = Path("/tmp/test_clustering")
TMP.mkdir(exist_ok=True)


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.write_text(content)
    return p


CSV_NUMERIC = (
    "x,y,z\n"
    "1.0,2.0,3.0\n"
    "1.1,2.1,3.1\n"
    "5.0,6.0,7.0\n"
    "5.1,6.1,7.1\n"
    "9.0,10.0,11.0\n"
    "9.1,10.1,11.1\n"
)

CSV_WITH_LABEL = (
    "x,y,label\n"
    "1.0,2.0,cat\n"
    "1.1,2.1,cat\n"
    "5.0,6.0,dog\n"
    "5.1,6.1,dog\n"
)

CSV_MIXED = (
    "x,text,y\n"
    "1.0,hello,2.0\n"
    "3.0,world,4.0\n"
    "5.0,foo,6.0\n"
)


@unittest.skipUnless(HAS_DEPS, "sklearn/numpy not installed")
class TestLoadNumericCSV(unittest.TestCase):
    def test_loads_numeric_columns(self):
        p = write("numeric.csv", CSV_NUMERIC)
        X, names = load_numeric_csv(p)
        self.assertEqual(X.shape, (6, 3))
        self.assertIn("x", names)

    def test_excludes_label_col(self):
        p = write("labeled.csv", CSV_WITH_LABEL)
        X, names = load_numeric_csv(p)
        self.assertNotIn("label", names)
        self.assertEqual(X.shape[1], 2)

    def test_excludes_non_numeric(self):
        p = write("mixed.csv", CSV_MIXED)
        X, names = load_numeric_csv(p)
        self.assertNotIn("text", names)
        self.assertEqual(X.shape[1], 2)

    def test_no_numeric_raises(self):
        p = write("alltext.csv", "a,b\nhello,world\nfoo,bar\n")
        with self.assertRaises(ValueError):
            load_numeric_csv(p)


@unittest.skipUnless(HAS_DEPS, "sklearn/numpy not installed")
class TestPreprocess(unittest.TestCase):
    def test_output_shape_preserved(self):
        p = write("numeric.csv", CSV_NUMERIC)
        X, _ = load_numeric_csv(p)
        X_proc = preprocess(X)
        self.assertEqual(X_proc.shape, X.shape)

    def test_output_mean_near_zero(self):
        p = write("numeric.csv", CSV_NUMERIC)
        X, _ = load_numeric_csv(p)
        X_proc = preprocess(X)
        means = X_proc.mean(axis=0)
        for m in means:
            self.assertAlmostEqual(m, 0.0, places=5)


class TestReportGeneration(unittest.TestCase):
    def _make_results(self):
        r1 = ClusterResult(
            name="K-Means", n_clusters=3,
            silhouette=0.72, calinski=150.0, davies=0.35,
            labels=[0, 0, 1, 1, 2, 2],
        )
        r2 = ClusterResult(
            name="Agglomerative", n_clusters=3,
            silhouette=0.68, calinski=140.0, davies=0.40,
            labels=[0, 0, 1, 1, 2, 2],
        )
        r3 = ClusterResult(
            name="DBSCAN", n_clusters=2,
            silhouette=0.60, calinski=120.0, davies=0.50,
            labels=[0, 0, 1, 1, -1, -1], n_noise=2,
        )
        return [r1, r2, r3]

    def test_report_has_algorithm_names(self):
        results = self._make_results()
        report = generate_report(results, Path("data.csv"), 6, 3,
                                 None, None, None, None, None)
        self.assertIn("K-Means", report)
        self.assertIn("Agglomerative", report)
        self.assertIn("DBSCAN", report)

    def test_report_has_sections(self):
        results = self._make_results()
        report = generate_report(results, Path("data.csv"), 6, 3,
                                 None, None, None, None, None)
        self.assertIn("## B. Algorithm Comparison", report)
        self.assertIn("## D. Interpretation Guide", report)

    def test_report_has_k_table_when_find_k(self):
        results = self._make_results()
        report = generate_report(
            results, Path("data.csv"), 6, 3,
            range(2, 5), [100.0, 80.0, 60.0], [0.5, 0.7, 0.6], 3, None,
        )
        self.assertIn("## A. Optimal K Analysis", report)
        self.assertIn("Recommended K = 3", report)

    def test_best_algorithm_highlighted(self):
        results = self._make_results()
        report = generate_report(results, Path("data.csv"), 6, 3,
                                 None, None, None, None, None)
        self.assertIn("Best algorithm by silhouette: K-Means", report)

    def test_noise_shown_for_dbscan(self):
        results = self._make_results()
        report = generate_report(results, Path("data.csv"), 6, 3,
                                 None, None, None, None, None)
        self.assertIn("noise pts", report)


if __name__ == "__main__":
    unittest.main(verbosity=2)
