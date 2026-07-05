#!/usr/bin/env python3
"""Tests for class_weights_calculator.py"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from class_weights_calculator import (
    count_csv_classes, count_json_classes, count_image_classes,
    compute_weights, compute_inverse_freq_weights, generate_report,
)

TMP = Path("/tmp/test_class_weights")
TMP.mkdir(exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


CSV_BALANCED = "img,label\na.jpg,cat\nb.jpg,cat\nc.jpg,dog\nd.jpg,dog\n"
CSV_IMBALANCED = "img,label\n" + "a.jpg,cat\n" * 50 + "b.jpg,dog\n" * 5
CSV_CUSTOM_COL = "img,defective\na.jpg,yes\nb.jpg,no\nc.jpg,yes\n"

COCO_JSON = json.dumps({
    "images": [{"id": 1}, {"id": 2}, {"id": 3}],
    "categories": [{"id": 1, "name": "cat"}, {"id": 2, "name": "dog"}],
    "annotations": [
        {"id": 1, "image_id": 1, "category_id": 1},
        {"id": 2, "image_id": 1, "category_id": 1},
        {"id": 3, "image_id": 2, "category_id": 2},
    ],
})

FLAT_JSON = json.dumps({"img1.jpg": "cat", "img2.jpg": "cat", "img3.jpg": "dog"})


class TestCountCSV(unittest.TestCase):
    def test_balanced_counts(self):
        p = write("balanced.csv", CSV_BALANCED)
        counts = count_csv_classes(p, None)
        self.assertEqual(counts["cat"], 2)
        self.assertEqual(counts["dog"], 2)

    def test_custom_label_col(self):
        p = write("custom.csv", CSV_CUSTOM_COL)
        counts = count_csv_classes(p, "defective")
        self.assertEqual(counts["yes"], 2)
        self.assertEqual(counts["no"], 1)

    def test_no_label_col_raises(self):
        p = write("nolabel.csv", "feature_a,feature_b\n1,2\n3,4\n")
        with self.assertRaises(ValueError):
            count_csv_classes(p, None)

    def test_imbalanced_counts(self):
        p = write("imbalanced.csv", CSV_IMBALANCED)
        counts = count_csv_classes(p, None)
        self.assertEqual(counts["cat"], 50)
        self.assertEqual(counts["dog"], 5)


class TestCountJSON(unittest.TestCase):
    def test_coco_format(self):
        p = write("coco.json", COCO_JSON)
        counts = count_json_classes(p)
        self.assertEqual(counts["cat"], 2)
        self.assertEqual(counts["dog"], 1)

    def test_flat_dict_format(self):
        p = write("flat.json", FLAT_JSON)
        counts = count_json_classes(p)
        self.assertEqual(counts["cat"], 2)
        self.assertEqual(counts["dog"], 1)

    def test_list_format(self):
        data = json.dumps([
            {"image": "a.jpg", "label": "cat"},
            {"image": "b.jpg", "label": "dog"},
            {"image": "c.jpg", "label": "cat"},
        ])
        p = write("list.json", data)
        counts = count_json_classes(p)
        self.assertEqual(counts["cat"], 2)
        self.assertEqual(counts["dog"], 1)


class TestCountImages(unittest.TestCase):
    def setUp(self):
        self.img_dir = TMP / "images"
        self.img_dir.mkdir(exist_ok=True)
        for cls, n in [("cat", 10), ("dog", 5)]:
            cls_dir = self.img_dir / cls
            cls_dir.mkdir(exist_ok=True)
            for i in range(n):
                (cls_dir / f"{i}.jpg").write_bytes(b"\xff")

    def test_class_counts(self):
        counts = count_image_classes(self.img_dir)
        self.assertEqual(counts["cat"], 10)
        self.assertEqual(counts["dog"], 5)

    def test_no_subdirs_raises(self):
        flat = TMP / "flat_images"
        flat.mkdir(exist_ok=True)
        (flat / "img.jpg").write_bytes(b"\xff")
        with self.assertRaises(ValueError):
            count_image_classes(flat)


class TestComputeWeights(unittest.TestCase):
    def test_balanced_weights_equal(self):
        counts = {"cat": 50, "dog": 50}
        weights = compute_weights(counts)
        self.assertAlmostEqual(weights["cat"], weights["dog"])

    def test_minority_gets_higher_weight(self):
        counts = {"cat": 90, "dog": 10}
        weights = compute_weights(counts)
        self.assertGreater(weights["dog"], weights["cat"])

    def test_balanced_formula(self):
        # n=100, k=2, count_cat=50 → weight = 100/(2*50) = 1.0
        counts = {"cat": 50, "dog": 50}
        weights = compute_weights(counts)
        self.assertAlmostEqual(weights["cat"], 1.0)

    def test_inverse_freq_sums_to_one(self):
        counts = {"cat": 60, "dog": 30, "bird": 10}
        weights = compute_inverse_freq_weights(counts)
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_inverse_freq_minority_highest(self):
        counts = {"majority": 90, "minority": 10}
        weights = compute_inverse_freq_weights(counts)
        self.assertGreater(weights["minority"], weights["majority"])


class TestReport(unittest.TestCase):
    def test_report_contains_class_names(self):
        counts = {"cat": 80, "dog": 20}
        wb = compute_weights(counts)
        wi = compute_inverse_freq_weights(counts)
        report = generate_report(counts, wb, wi, Path("data"))
        self.assertIn("cat", report)
        self.assertIn("dog", report)

    def test_report_contains_python_code(self):
        counts = {"a": 50, "b": 50}
        wb = compute_weights(counts)
        wi = compute_inverse_freq_weights(counts)
        report = generate_report(counts, wb, wi, Path("data"))
        self.assertIn("CrossEntropyLoss", report)
        self.assertIn("torch.tensor", report)

    def test_imbalance_warning_in_report(self):
        counts = {"majority": 95, "minority": 5}
        wb = compute_weights(counts)
        wi = compute_inverse_freq_weights(counts)
        report = generate_report(counts, wb, wi, Path("data"))
        self.assertIn("Severe", report)

    def test_balanced_positive_note(self):
        counts = {"a": 50, "b": 55}
        wb = compute_weights(counts)
        wi = compute_inverse_freq_weights(counts)
        report = generate_report(counts, wb, wi, Path("data"))
        self.assertIn("balanced", report.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
