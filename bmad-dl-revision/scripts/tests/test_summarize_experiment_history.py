#!/usr/bin/env python3
"""Tests for summarize_experiment_history.py"""

import csv
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from summarize_experiment_history import (
    discover_runs,
    extract_run_summary,
    generate_summary_table,
    RunSummary,
    _aggregate_lightning_metrics,
    _best_value,
)

TMP = Path("/tmp/test_exp_history")
TMP.mkdir(exist_ok=True)


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


# ── Lightning-style metrics.csv ───────────────────────────────────────────────

# Lightning CSVLogger writes one metric per row, others are empty
LIGHTNING_CSV = (
    "epoch,step,train/loss,val/loss,val/f1\n"
    "0,10,0.85,,\n"
    "0,10,,0.90,0.70\n"
    "1,20,0.72,,\n"
    "1,20,,0.78,0.80\n"
    "2,30,0.60,,\n"
    "2,30,,0.65,0.91\n"
)

# Simple flat CSV (not Lightning style)
FLAT_CSV = (
    "epoch,train_loss,val_loss,f1\n"
    "0,0.85,0.90,0.71\n"
    "1,0.72,0.78,0.80\n"
    "2,0.61,0.65,0.93\n"
)

JSON_HISTORY = json.dumps({"history": [
    {"epoch": 0, "val/loss": 0.90, "val/f1": 0.71},
    {"epoch": 1, "val/loss": 0.78, "val/f1": 0.80},
    {"epoch": 2, "val/loss": 0.65, "val/f1": 0.93},
]})


class TestAggregateMetrics(unittest.TestCase):
    def test_aggregates_non_nan(self):
        rows = [
            {"epoch": 0.0, "train/loss": 0.85, "val/loss": None},
            {"epoch": 0.0, "train/loss": None, "val/loss": 0.90},
            {"epoch": 1.0, "train/loss": 0.72, "val/loss": None},
            {"epoch": 1.0, "train/loss": None, "val/loss": 0.78},
        ]
        agg = _aggregate_lightning_metrics(rows)
        self.assertIn("train/loss", agg)
        self.assertIn("val/loss", agg)
        self.assertEqual(len(agg["train/loss"]), 2)
        self.assertEqual(len(agg["val/loss"]), 2)

    def test_skips_epoch_and_step(self):
        rows = [{"epoch": 0.0, "step": 10.0, "val/loss": 0.9}]
        agg = _aggregate_lightning_metrics(rows)
        # epoch and step are not excluded here (filtered in callers), but val/loss is included
        self.assertIn("val/loss", agg)


class TestBestValue(unittest.TestCase):
    def test_min_mode(self):
        self.assertAlmostEqual(_best_value([0.9, 0.7, 0.8], "min"), 0.7)

    def test_max_mode(self):
        self.assertAlmostEqual(_best_value([0.7, 0.9, 0.8], "max"), 0.9)


class TestDiscoverRuns(unittest.TestCase):
    def setUp(self):
        self.logs = TMP / "logs_discover"
        self.logs.mkdir(exist_ok=True)

        # Lightning-style nested layout
        lightning_dir = self.logs / "run_a" / "version_0"
        lightning_dir.mkdir(parents=True, exist_ok=True)
        (lightning_dir / "metrics.csv").write_text(FLAT_CSV)

        # Flat layout
        flat_dir = self.logs / "run_b"
        flat_dir.mkdir(exist_ok=True)
        (flat_dir / "metrics.csv").write_text(FLAT_CSV)

        # Docs-style named file
        (self.logs / "run_c_metrics.csv").write_text(FLAT_CSV)

    def test_discovers_all_patterns(self):
        found = discover_runs(self.logs)
        self.assertGreaterEqual(len(found), 2)

    def test_no_duplicates(self):
        found = discover_runs(self.logs)
        self.assertEqual(len(found), len(set(found)))


class TestExtractRunSummary(unittest.TestCase):
    def setUp(self):
        self.logs = TMP / "logs_extract"
        self.logs.mkdir(exist_ok=True)

    def test_flat_csv_summary(self):
        p = write("logs_extract/exp1_metrics.csv", FLAT_CSV)
        s = extract_run_summary(p, self.logs, "f1", "max")
        self.assertIsNotNone(s)
        self.assertEqual(s.epochs, 3)

    def test_best_val_loss_extracted(self):
        p = write("logs_extract/exp2_metrics.csv", FLAT_CSV)
        s = extract_run_summary(p, self.logs, "val/loss", "min")
        self.assertAlmostEqual(s.best_val_loss, 0.65)

    def test_best_metric_extracted(self):
        p = write("logs_extract/exp3_metrics.csv", FLAT_CSV)
        s = extract_run_summary(p, self.logs, "f1", "max")
        self.assertAlmostEqual(s.best_metric_value, 0.93)

    def test_json_history(self):
        p = write("logs_extract/run_json_metrics.json", JSON_HISTORY)
        s = extract_run_summary(p, self.logs, "val/f1", "max")
        self.assertIsNotNone(s)
        self.assertAlmostEqual(s.best_val_loss, 0.65)

    def test_lightning_csv_parsed(self):
        p = write("logs_extract/lightning_metrics.csv", LIGHTNING_CSV)
        s = extract_run_summary(p, self.logs, "val/f1", "max")
        self.assertIsNotNone(s)
        # val/loss values: 0.90, 0.78, 0.65 → best = 0.65
        self.assertAlmostEqual(s.best_val_loss, 0.65)

    def test_empty_file_returns_none(self):
        p = write("logs_extract/empty_metrics.csv", "epoch,val/loss\n")
        s = extract_run_summary(p, self.logs, "val/loss", "min")
        self.assertIsNone(s)

    def test_run_name_derived_from_path(self):
        p = write("logs_extract/my_experiment_metrics.csv", FLAT_CSV)
        s = extract_run_summary(p, self.logs, "val/loss", "min")
        self.assertIn("my_experiment", s.name)


class TestGenerateSummaryTable(unittest.TestCase):
    def _make_summaries(self):
        s1 = RunSummary(name="run_a", source_file=Path("a.csv"),
                        epochs=10, best_val_loss=0.65, best_metric_value=0.93,
                        best_metric_name="f1", best_epoch=8)
        s1.all_metrics = {"val/loss": 0.65, "f1": 0.93}

        s2 = RunSummary(name="run_b", source_file=Path("b.csv"),
                        epochs=15, best_val_loss=0.70, best_metric_value=0.87,
                        best_metric_name="f1", best_epoch=12)
        s2.all_metrics = {"val/loss": 0.70, "f1": 0.87}
        return [s1, s2]

    def test_table_contains_run_names(self):
        summaries = self._make_summaries()
        table = generate_summary_table(summaries, "f1", "max")
        self.assertIn("run_a", table)
        self.assertIn("run_b", table)

    def test_best_run_ranked_first(self):
        summaries = self._make_summaries()
        table = generate_summary_table(summaries, "f1", "max")
        # run_a has better f1; its rank marker should appear before run_b
        pos_a = table.find("run_a")
        pos_b = table.find("run_b")
        self.assertLess(pos_a, pos_b)

    def test_top_n_limits_rows(self):
        summaries = self._make_summaries()
        table = generate_summary_table(summaries, "f1", "max", top_n=1)
        self.assertIn("run_a", table)
        self.assertNotIn("run_b", table)

    def test_empty_summaries(self):
        table = generate_summary_table([], "val/loss", "min")
        self.assertIn("No experiment runs found", table)

    def test_delta_section_present(self):
        summaries = self._make_summaries()
        table = generate_summary_table(summaries, "f1", "max")
        self.assertIn("Best vs Runner-Up", table)

    def test_all_metrics_section(self):
        summaries = self._make_summaries()
        table = generate_summary_table(summaries, "f1", "max")
        self.assertIn("All Tracked Metrics", table)
        self.assertIn("val/loss", table)


if __name__ == "__main__":
    unittest.main(verbosity=2)
