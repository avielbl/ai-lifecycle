#!/usr/bin/env python3
"""Tests for plot_training_curves.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from plot_training_curves import load_metrics, group_metrics, _best_epoch, _is_train

try:
    import matplotlib
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

TMP = Path("/tmp/test_curves")
TMP.mkdir(exist_ok=True)


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.write_text(content)
    return p


# Lightning sparse format (one metric per row)
LIGHTNING_CSV = (
    "epoch,step,train/loss,val/loss,val/f1\n"
    "0,10,0.85,,\n"
    "0,10,,0.90,0.70\n"
    "1,20,0.72,,\n"
    "1,20,,0.78,0.80\n"
    "2,30,0.60,,\n"
    "2,30,,0.65,0.91\n"
)

# Flat format (one row per epoch)
FLAT_CSV = (
    "epoch,train_loss,val_loss,f1\n"
    "0,0.85,0.90,0.71\n"
    "1,0.72,0.78,0.80\n"
    "2,0.61,0.65,0.93\n"
)


class TestLoadMetrics(unittest.TestCase):
    def test_flat_csv_loads(self):
        p = write("flat.csv", FLAT_CSV)
        metrics = load_metrics(p)
        self.assertIn("train_loss", metrics)
        self.assertIn("val_loss", metrics)
        self.assertEqual(len(metrics["val_loss"]), 3)

    def test_flat_csv_values(self):
        p = write("flat.csv", FLAT_CSV)
        metrics = load_metrics(p)
        self.assertAlmostEqual(metrics["val_loss"][0], 0.90)
        self.assertAlmostEqual(metrics["val_loss"][2], 0.65)

    def test_lightning_sparse_aggregated(self):
        p = write("lightning.csv", LIGHTNING_CSV)
        metrics = load_metrics(p)
        # Should aggregate: val/loss has 3 values (one per epoch)
        self.assertIn("val/loss", metrics)
        self.assertEqual(len(metrics["val/loss"]), 3)
        self.assertAlmostEqual(metrics["val/loss"][0], 0.90)
        self.assertAlmostEqual(metrics["val/loss"][2], 0.65)

    def test_lightning_train_loss(self):
        p = write("lightning.csv", LIGHTNING_CSV)
        metrics = load_metrics(p)
        self.assertIn("train/loss", metrics)
        self.assertAlmostEqual(metrics["train/loss"][0], 0.85)

    def test_empty_file_raises(self):
        p = write("empty.csv", "epoch,val/loss\n")
        with self.assertRaises(ValueError):
            load_metrics(p)


class TestGroupMetrics(unittest.TestCase):
    def test_loss_grouped_together(self):
        metrics = {
            "train/loss": [0.9, 0.8, 0.7],
            "val/loss": [0.95, 0.85, 0.75],
            "val/f1": [0.60, 0.75, 0.82],
        }
        groups = group_metrics(metrics)
        self.assertIn("loss", groups)
        self.assertIn("train/loss", groups["loss"])
        self.assertIn("val/loss", groups["loss"])

    def test_non_loss_gets_own_group(self):
        metrics = {
            "val/loss": [0.9, 0.8],
            "val/f1": [0.6, 0.8],
        }
        groups = group_metrics(metrics)
        # f1 should have its own group
        found_f1 = any("f1" in k.lower() for k in groups)
        self.assertTrue(found_f1)

    def test_empty_loss_group_removed(self):
        metrics = {"val/f1": [0.6, 0.8], "val/acc": [0.7, 0.9]}
        groups = group_metrics(metrics)
        self.assertNotIn("loss", groups)


class TestHelpers(unittest.TestCase):
    def test_is_train_true(self):
        self.assertTrue(_is_train("train/loss"))
        self.assertTrue(_is_train("train_loss"))

    def test_is_train_false_for_val(self):
        self.assertFalse(_is_train("val/loss"))
        self.assertFalse(_is_train("val_f1"))

    def test_best_epoch_min(self):
        values = [0.9, 0.7, 0.65, 0.72]
        self.assertEqual(_best_epoch(values, "min"), 2)

    def test_best_epoch_max(self):
        values = [0.6, 0.75, 0.93, 0.91]
        self.assertEqual(_best_epoch(values, "max"), 2)

    def test_best_epoch_with_nan(self):
        values = [float("nan"), 0.8, 0.65]
        self.assertEqual(_best_epoch(values, "min"), 2)

    def test_best_epoch_all_nan_returns_none(self):
        values = [float("nan"), float("nan")]
        self.assertIsNone(_best_epoch(values, "min"))


@unittest.skipUnless(HAS_MPL, "matplotlib not installed")
class TestPlottingIntegration(unittest.TestCase):
    def test_flat_csv_plot_saved(self):
        from plot_training_curves import plot_curves
        p = write("flat.csv", FLAT_CSV)
        metrics = load_metrics(p)
        out = TMP / "test_output_curves.png"
        plot_curves(metrics, "Test Run", out)
        self.assertTrue(out.exists())
        self.assertGreater(out.stat().st_size, 0)

    def test_lightning_csv_plot_saved(self):
        from plot_training_curves import plot_curves
        p = write("lightning.csv", LIGHTNING_CSV)
        metrics = load_metrics(p)
        out = TMP / "test_lightning_curves.png"
        plot_curves(metrics, "Lightning Run", out)
        self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
