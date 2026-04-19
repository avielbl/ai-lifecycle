#!/usr/bin/env python3
"""Tests for plot_confusion_matrix.py"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from plot_confusion_matrix import (
    load_predictions_csv, load_label_files, generate_markdown,
)

try:
    import matplotlib
    import sklearn
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

TMP = Path("/tmp/test_confmat")
TMP.mkdir(exist_ok=True)


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.write_text(content)
    return p


PREDS_CSV = (
    "y_true,y_pred,y_score\n"
    "cat,cat,0.95\n"
    "cat,cat,0.87\n"
    "dog,dog,0.91\n"
    "dog,cat,0.45\n"
    "cat,dog,0.38\n"
)

PREDS_CUSTOM_COLS = (
    "actual,prediction\n"
    "cat,cat\n"
    "dog,dog\n"
    "cat,dog\n"
)


class TestLoadPredictionsCSV(unittest.TestCase):
    def test_standard_cols(self):
        p = write("preds.csv", PREDS_CSV)
        y_true, y_pred = load_predictions_csv(p, "y_true", "y_pred")
        self.assertEqual(len(y_true), 5)
        self.assertEqual(y_true[0], "cat")
        self.assertEqual(y_pred[3], "cat")

    def test_auto_detect_custom_cols(self):
        p = write("custom.csv", PREDS_CUSTOM_COLS)
        # Should auto-detect 'actual' → y_true, 'prediction' → y_pred
        y_true, y_pred = load_predictions_csv(p, "y_true", "y_pred")
        self.assertEqual(len(y_true), 3)

    def test_missing_col_raises(self):
        p = write("bad.csv", "col_a,col_b\n1,2\n3,4\n")
        with self.assertRaises(ValueError):
            load_predictions_csv(p, "y_true", "y_pred")

    def test_empty_file_raises(self):
        p = write("empty.csv", "y_true,y_pred\n")
        with self.assertRaises(ValueError):
            load_predictions_csv(p, "y_true", "y_pred")


class TestLoadLabelFiles(unittest.TestCase):
    def test_loads_matching_files(self):
        true_f = write("true.txt", "cat\ncat\ndog\ndog\n")
        pred_f = write("pred.txt", "cat\ncat\ndog\ncat\n")
        y_true, y_pred = load_label_files(true_f, pred_f)
        self.assertEqual(len(y_true), 4)
        self.assertEqual(y_pred[3], "cat")

    def test_length_mismatch_raises(self):
        true_f = write("true2.txt", "cat\ndog\n")
        pred_f = write("pred2.txt", "cat\n")
        with self.assertRaises(ValueError):
            load_label_files(true_f, pred_f)

    def test_ignores_empty_lines(self):
        true_f = write("true3.txt", "cat\ndog\n\n")
        pred_f = write("pred3.txt", "cat\ncat\n\n")
        y_true, y_pred = load_label_files(true_f, pred_f)
        self.assertEqual(len(y_true), 2)


@unittest.skipUnless(HAS_DEPS, "matplotlib/sklearn not installed")
class TestGenerateMarkdown(unittest.TestCase):
    def _preds(self):
        return (
            ["cat", "cat", "dog", "dog", "cat", "dog"],
            ["cat", "cat", "dog", "cat", "cat", "dog"],
        )

    def test_markdown_has_accuracy(self):
        y_true, y_pred = self._preds()
        md = generate_markdown(y_true, y_pred, ["cat", "dog"], None, None)
        self.assertIn("Accuracy", md)

    def test_markdown_has_class_table(self):
        y_true, y_pred = self._preds()
        md = generate_markdown(y_true, y_pred, ["cat", "dog"], None, None)
        self.assertIn("| cat |", md)
        self.assertIn("| dog |", md)

    def test_markdown_includes_classification_report(self):
        y_true, y_pred = self._preds()
        md = generate_markdown(y_true, y_pred, ["cat", "dog"], None, None)
        self.assertIn("Classification Report", md)

    def test_markdown_includes_image_links_when_paths_given(self):
        y_true, y_pred = self._preds()
        cm_path = Path("confusion_matrix.png")
        md_path = Path("metrics.png")
        md = generate_markdown(y_true, y_pred, ["cat", "dog"], cm_path, md_path)
        self.assertIn("confusion_matrix.png", md)
        self.assertIn("metrics.png", md)


@unittest.skipUnless(HAS_DEPS, "matplotlib/sklearn not installed")
class TestPlottingIntegration(unittest.TestCase):
    def setUp(self):
        self.p = write("preds.csv", PREDS_CSV)
        self.y_true = ["cat", "cat", "dog", "dog", "cat"]
        self.y_pred = ["cat", "cat", "dog", "cat", "cat"]
        self.classes = ["cat", "dog"]

    def test_confusion_matrix_saved(self):
        from plot_confusion_matrix import plot_confusion_matrix
        out = TMP / "test_cm.png"
        plot_confusion_matrix(self.y_true, self.y_pred, self.classes, out)
        self.assertTrue(out.exists())
        self.assertGreater(out.stat().st_size, 0)

    def test_per_class_metrics_saved(self):
        from plot_confusion_matrix import plot_per_class_metrics
        out = TMP / "test_metrics.png"
        plot_per_class_metrics(self.y_true, self.y_pred, self.classes, out)
        self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
