#!/usr/bin/env python3
"""Tests for eda_analyzer.py"""

import csv
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from eda_analyzer import (
    detect_format,
    analyze,
    analyze_csv,
    analyze_json_annotations,
    generate_markdown_report,
    EDAReport,
    ClassInfo,
)

TMP = Path("/tmp/test_eda")
TMP.mkdir(exist_ok=True)


def write(name: str, content: str) -> Path:
    p = TMP / name
    p.write_text(content)
    return p


# ── Format detection ──────────────────────────────────────────────────────────

class TestDetectFormat(unittest.TestCase):
    def test_csv(self):
        p = write("data.csv", "a,b\n1,2\n")
        self.assertEqual(detect_format(p), "csv")

    def test_tsv(self):
        p = write("data.tsv", "a\tb\n1\t2\n")
        self.assertEqual(detect_format(p), "csv")

    def test_json(self):
        p = write("labels.json", "{}")
        self.assertEqual(detect_format(p), "json_annotations")

    def test_npy(self):
        p = write("arr.npy", "")
        self.assertEqual(detect_format(p), "numpy")

    def test_npz(self):
        p = write("arr.npz", "")
        self.assertEqual(detect_format(p), "numpy")

    def test_hdf5(self):
        p = write("data.h5", "")
        self.assertEqual(detect_format(p), "hdf5")

    def test_unknown_extension(self):
        p = write("data.xyz", "content")
        self.assertEqual(detect_format(p), "unknown")

    def test_image_dir(self):
        img_dir = TMP / "img_dataset"
        img_dir.mkdir(exist_ok=True)
        (img_dir / "cat.jpg").write_bytes(b"fake")
        self.assertEqual(detect_format(img_dir), "image_dir")

    def test_non_image_dir(self):
        empty_dir = TMP / "noimg"
        empty_dir.mkdir(exist_ok=True)
        (empty_dir / "notes.txt").write_text("hi")
        self.assertIn(detect_format(empty_dir), ("image_dir", "unknown_dir"))


# ── CSV analysis ──────────────────────────────────────────────────────────────

CSV_BALANCED = (
    "image,label,feature1,feature2\n"
    "a.jpg,cat,0.1,0.2\n"
    "b.jpg,cat,0.3,0.4\n"
    "c.jpg,dog,0.5,0.6\n"
    "d.jpg,dog,0.7,0.8\n"
)

CSV_IMBALANCED = (
    "image,label\n"
    + "a.jpg,cat\n" * 50
    + "b.jpg,dog\n" * 5
)

CSV_MISSING = (
    "a,b,label\n"
    "1,,cat\n"
    "2,2,\n"
    "3,3,dog\n"
)


class TestCSVAnalysis(unittest.TestCase):
    def test_basic_parse(self):
        p = write("balanced.csv", CSV_BALANCED)
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertEqual(report.num_rows, 4)
        self.assertEqual(report.num_cols, 4)

    def test_label_distribution(self):
        p = write("balanced.csv", CSV_BALANCED)
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertEqual(report.label_distribution["cat"], 2)
        self.assertEqual(report.label_distribution["dog"], 2)

    def test_missing_values_detected(self):
        p = write("missing.csv", CSV_MISSING)
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertIn("b", report.missing_values)
        self.assertIn("label", report.missing_values)

    def test_imbalance_warning(self):
        p = write("imbalanced.csv", CSV_IMBALANCED)
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertTrue(any("imbalance" in w.lower() for w in report.warnings))

    def test_columns_captured(self):
        p = write("balanced.csv", CSV_BALANCED)
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertIn("label", report.columns)
        self.assertIn("feature1", report.columns)

    def test_empty_csv(self):
        p = write("empty.csv", "col1,col2\n")
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertTrue(report.errors)

    def test_no_label_column_warning(self):
        p = write("nolabel.csv", "feature_a,feature_b\n1,2\n3,4\n")
        report = EDAReport(data_path=p, format_detected="")
        analyze_csv(p, report)
        self.assertTrue(any("label" in w.lower() for w in report.warnings))


# ── JSON annotation analysis ──────────────────────────────────────────────────

COCO_JSON = json.dumps({
    "images": [{"id": 1}, {"id": 2}, {"id": 3}],
    "categories": [{"id": 1, "name": "cat"}, {"id": 2, "name": "dog"}],
    "annotations": [
        {"id": 1, "image_id": 1, "category_id": 1},
        {"id": 2, "image_id": 1, "category_id": 1},
        {"id": 3, "image_id": 2, "category_id": 2},
    ],
})

FLAT_DICT_JSON = json.dumps({
    "img1.jpg": "cat",
    "img2.jpg": "cat",
    "img3.jpg": "dog",
})

LIST_JSON = json.dumps([
    {"image": "a.jpg", "label": "cat"},
    {"image": "b.jpg", "label": "cat"},
    {"image": "c.jpg", "label": "dog"},
])


class TestJSONAnnotations(unittest.TestCase):
    def test_coco_format(self):
        p = write("coco.json", COCO_JSON)
        report = EDAReport(data_path=p, format_detected="")
        analyze_json_annotations(p, report)
        self.assertEqual(report.annotation_count, 3)
        self.assertIn("cat", report.annotation_classes)
        self.assertEqual(report.annotation_classes["cat"], 2)

    def test_coco_unannotated_images(self):
        p = write("coco.json", COCO_JSON)
        report = EDAReport(data_path=p, format_detected="")
        analyze_json_annotations(p, report)
        # image_id=3 has no annotation
        self.assertEqual(report.images_without_annotations, 1)
        self.assertTrue(any("no annotations" in w.lower() for w in report.warnings))

    def test_flat_dict_format(self):
        p = write("flat.json", FLAT_DICT_JSON)
        report = EDAReport(data_path=p, format_detected="")
        analyze_json_annotations(p, report)
        self.assertEqual(report.annotation_count, 3)
        self.assertEqual(report.annotation_classes["cat"], 2)

    def test_list_format(self):
        p = write("list.json", LIST_JSON)
        report = EDAReport(data_path=p, format_detected="")
        analyze_json_annotations(p, report)
        self.assertEqual(report.annotation_count, 3)
        self.assertEqual(report.annotation_classes["dog"], 1)


# ── Image directory analysis ──────────────────────────────────────────────────

class TestImageDirAnalysis(unittest.TestCase):
    def setUp(self):
        self.ds = TMP / "ds_class"
        self.ds.mkdir(exist_ok=True)
        for cls in ("cat", "dog"):
            cls_dir = self.ds / cls
            cls_dir.mkdir(exist_ok=True)
            for i in range(5):
                (cls_dir / f"{cls}_{i}.jpg").write_bytes(b"\xff\xd8\xff")  # fake JPEG header

    def test_class_dirs_detected(self):
        report = analyze(self.ds)
        class_names = [c.name for c in report.classes]
        self.assertIn("cat", class_names)
        self.assertIn("dog", class_names)

    def test_total_images(self):
        report = analyze(self.ds)
        self.assertEqual(report.total_images, 10)

    def test_format_detected(self):
        report = analyze(self.ds)
        self.assertIn("Image", report.format_detected)


class TestImageDirWithSplits(unittest.TestCase):
    def setUp(self):
        self.ds = TMP / "ds_splits"
        self.ds.mkdir(exist_ok=True)
        for split in ("train", "val"):
            split_dir = self.ds / split
            split_dir.mkdir(exist_ok=True)
            for cls in ("cat", "dog"):
                cls_dir = split_dir / cls
                cls_dir.mkdir(exist_ok=True)
                count = 8 if split == "train" else 2
                for i in range(count):
                    (cls_dir / f"{i}.jpg").write_bytes(b"\xff")

    def test_splits_detected(self):
        report = analyze(self.ds, split_names=["train", "val"])
        self.assertIn("train", report.splits_found)
        self.assertIn("val", report.splits_found)

    def test_split_counts(self):
        report = analyze(self.ds, split_names=["train", "val"])
        self.assertEqual(report.splits_found["train"], 16)
        self.assertEqual(report.splits_found["val"], 4)


class TestClassImbalance(unittest.TestCase):
    def setUp(self):
        self.ds = TMP / "ds_imbalanced"
        self.ds.mkdir(exist_ok=True)
        # Create 50:5 imbalance
        for cls, count in (("majority", 50), ("minority", 5)):
            cls_dir = self.ds / cls
            cls_dir.mkdir(exist_ok=True)
            for i in range(count):
                (cls_dir / f"{i}.jpg").write_bytes(b"\xff")

    def test_severe_imbalance_warning(self):
        report = analyze(self.ds)
        self.assertTrue(any("imbalance" in w.lower() for w in report.warnings))


# ── Report generation ─────────────────────────────────────────────────────────

class TestMarkdownReport(unittest.TestCase):
    def _make_report(self):
        r = EDAReport(data_path=Path("/fake/data"), format_detected="CSV/Tabular Dataset")
        r.num_rows = 100
        r.num_cols = 5
        r.columns = ["x", "y", "label"]
        r.label_distribution = {"cat": 60, "dog": 40}
        return r

    def test_report_has_sections(self):
        report = self._make_report()
        md = generate_markdown_report(report)
        self.assertIn("## A. Dataset Overview", md)
        self.assertIn("## B. Class Distribution", md)
        self.assertIn("## C. Data Quality Assessment", md)
        self.assertIn("## D. Split Verification", md)
        self.assertIn("## F. EDA Summary for TSK-001", md)

    def test_report_has_class_data(self):
        report = self._make_report()
        md = generate_markdown_report(report)
        self.assertIn("cat", md)
        self.assertIn("dog", md)

    def test_report_has_warnings_section(self):
        report = self._make_report()
        report.warnings.append("Something is wrong")
        md = generate_markdown_report(report)
        self.assertIn("## E. Issues", md)
        self.assertIn("Something is wrong", md)

    def test_report_no_warnings_section_when_clean(self):
        report = self._make_report()
        md = generate_markdown_report(report)
        self.assertNotIn("## E. Issues", md)

    def test_image_classes_in_report(self):
        r = EDAReport(data_path=Path("/fake/images"), format_detected="Image Dataset")
        r.classes = [ClassInfo("cat", 50), ClassInfo("dog", 50)]
        r.total_images = 100
        md = generate_markdown_report(r)
        self.assertIn("cat", md)
        self.assertIn("50.0%", md)

    def test_split_no_dirs_warning(self):
        r = EDAReport(data_path=Path("/fake/images"), format_detected="Image Dataset")
        r.classes = [ClassInfo("cat", 50)]
        r.total_images = 50
        md = generate_markdown_report(r)
        self.assertIn("No explicit split", md)


# ── Full pipeline (analyze function) ─────────────────────────────────────────

class TestAnalyzePipeline(unittest.TestCase):
    def test_csv_pipeline(self):
        p = write("pipeline.csv", CSV_BALANCED)
        report = analyze(p)
        self.assertEqual(report.format_detected, "CSV/Tabular Dataset")
        self.assertEqual(report.num_rows, 4)

    def test_json_pipeline(self):
        p = write("pipeline.json", FLAT_DICT_JSON)
        report = analyze(p)
        self.assertEqual(report.format_detected, "JSON Annotations")
        self.assertEqual(report.annotation_count, 3)

    def test_unknown_format_error(self):
        p = write("data.xyz", "some content")
        report = analyze(p)
        self.assertTrue(report.errors)
        self.assertTrue(any("Unrecognized" in e for e in report.errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
