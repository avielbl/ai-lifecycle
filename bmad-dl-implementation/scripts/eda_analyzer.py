#!/usr/bin/env python3
"""
eda_analyzer.py — BMAD DL Lifecycle  (inspired by K-Dense claude-scientific-skills)
ML-focused Exploratory Data Analysis for common deep learning data formats.

Supported formats:
  - Image datasets  : directory of images (class-labeled subdirs or flat)
  - CSV / TSV       : tabular feature/label datasets
  - NumPy           : .npy / .npz arrays
  - HDF5            : .h5 / .hdf5 files
  - JSON annotations: COCO-style or flat label files

Generates a structured markdown EDA report aligned with TSK-001 requirements:
  class distributions, annotation quality, missing values, split verification.

Usage:
    python3 scripts/eda_analyzer.py <data_path> [--output report.md] [--splits train val test]
    python3 scripts/eda_analyzer.py data/images/ --splits train val test
    python3 scripts/eda_analyzer.py data/features.csv

Exit codes:
    0 — success, report written
    1 — warnings (partial data)
    2 — error
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


# ── Optional imports ───────────────────────────────────────────────────────────

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import csv as _csv
    HAS_CSV = True
except ImportError:
    HAS_CSV = False  # csv is stdlib, always available

HAS_PIL = False
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    pass

HAS_H5PY = False
try:
    import h5py
    HAS_H5PY = True
except ImportError:
    pass


# ── Data structures ────────────────────────────────────────────────────────────

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

@dataclass
class ClassInfo:
    name: str
    count: int
    sample_files: list[str] = field(default_factory=list)


@dataclass
class EDAReport:
    data_path: Path
    format_detected: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    # Image dataset
    total_images: int = 0
    classes: list[ClassInfo] = field(default_factory=list)
    image_sizes: list[tuple[int, int]] = field(default_factory=list)
    corrupt_files: list[str] = field(default_factory=list)
    splits_found: dict[str, int] = field(default_factory=dict)

    # Tabular
    num_rows: int = 0
    num_cols: int = 0
    columns: list[str] = field(default_factory=list)
    missing_values: dict[str, int] = field(default_factory=dict)
    label_distribution: dict[str, int] = field(default_factory=dict)
    numeric_stats: dict[str, dict[str, float]] = field(default_factory=dict)

    # NumPy
    array_shapes: list[tuple] = field(default_factory=list)
    array_dtypes: list[str] = field(default_factory=list)
    array_stats: dict[str, Any] = field(default_factory=dict)

    # HDF5
    hdf5_keys: list[str] = field(default_factory=list)
    hdf5_shapes: dict[str, tuple] = field(default_factory=dict)

    # Annotation JSON
    annotation_classes: dict[str, int] = field(default_factory=dict)
    annotation_count: int = 0
    images_without_annotations: int = 0


# ── Format detection ───────────────────────────────────────────────────────────

def detect_format(path: Path) -> str:
    if path.is_dir():
        # Check if it's an image dataset directory
        image_files = list(path.rglob("*"))
        if any(f.suffix.lower() in IMAGE_EXTENSIONS for f in image_files[:50]):
            return "image_dir"
        return "unknown_dir"
    suffix = path.suffix.lower()
    if suffix in (".csv", ".tsv"):
        return "csv"
    if suffix in (".npy", ".npz"):
        return "numpy"
    if suffix in (".h5", ".hdf5"):
        return "hdf5"
    if suffix == ".json":
        return "json_annotations"
    return "unknown"


# ── Image dataset analysis ─────────────────────────────────────────────────────

def analyze_image_dir(path: Path, report: EDAReport, split_names: list[str]) -> None:
    report.format_detected = "Image Dataset (directory)"

    # Check for split subdirectories
    subdirs = [d for d in path.iterdir() if d.is_dir()]
    split_dirs = [d for d in subdirs if d.name.lower() in (s.lower() for s in split_names)]

    if split_dirs:
        # Split-structured dataset: path/train/class/img.jpg
        for split_dir in split_dirs:
            class_dirs = [d for d in split_dir.iterdir() if d.is_dir()]
            split_count = sum(
                len([f for f in cd.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS])
                for cd in class_dirs
            )
            report.splits_found[split_dir.name] = split_count

        # Analyze class distribution from train split (or first split)
        ref_split = next((d for d in split_dirs if "train" in d.name.lower()), split_dirs[0])
        _analyze_class_structure(ref_split, report)
    else:
        # Flat or class-labeled directory: path/class/img.jpg
        _analyze_class_structure(path, report)

    report.total_images = sum(c.count for c in report.classes)

    # Sample image sizes
    if HAS_PIL:
        _sample_image_sizes(path, report)
    else:
        report.warnings.append(
            "PIL not installed — skipping image size and corruption checks. "
            "Install with: pip install Pillow"
        )

    # Class balance check
    if report.classes:
        counts = [c.count for c in report.classes]
        max_c, min_c = max(counts), min(counts)
        if min_c > 0 and max_c / min_c > 5:
            report.warnings.append(
                f"Severe class imbalance detected: ratio {max_c/min_c:.1f}:1 "
                f"({report.classes[counts.index(max_c)].name} vs "
                f"{report.classes[counts.index(min_c)].name}). "
                f"Consider oversampling, undersampling, or weighted loss."
            )
        elif min_c > 0 and max_c / min_c > 2:
            report.warnings.append(
                f"Moderate class imbalance: ratio {max_c/min_c:.1f}:1. "
                f"Monitor per-class metrics during training."
            )


def _analyze_class_structure(base_dir: Path, report: EDAReport) -> None:
    class_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    if class_dirs:
        for class_dir in sorted(class_dirs):
            images = [f for f in class_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
            report.classes.append(ClassInfo(
                name=class_dir.name,
                count=len(images),
                sample_files=[f.name for f in images[:3]],
            ))
    else:
        # Flat directory
        images = [f for f in base_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
        if images:
            report.classes.append(ClassInfo(name="(unlabeled)", count=len(images)))
            report.warnings.append(
                "No class subdirectories found — images appear unlabeled. "
                "Organize into class subdirectories for supervised training."
            )


def _sample_image_sizes(base_dir: Path, report: EDAReport, max_samples: int = 100) -> None:
    all_images = list(base_dir.rglob("*"))
    image_files = [f for f in all_images if f.suffix.lower() in IMAGE_EXTENSIONS][:max_samples]
    sizes: list[tuple[int, int]] = []

    for img_path in image_files:
        try:
            with Image.open(img_path) as img:
                sizes.append(img.size)  # (width, height)
        except Exception:
            report.corrupt_files.append(str(img_path.relative_to(base_dir)))

    report.image_sizes = sizes
    if report.corrupt_files:
        report.warnings.append(
            f"{len(report.corrupt_files)} corrupt or unreadable image(s) found."
        )

    if sizes:
        unique_sizes = set(sizes)
        if len(unique_sizes) > 1:
            report.warnings.append(
                f"Inconsistent image sizes detected: {len(unique_sizes)} unique sizes in sample. "
                f"Most common: {Counter(sizes).most_common(1)[0][0]}. "
                f"Consider resizing to a fixed resolution."
            )


# ── CSV / tabular analysis ─────────────────────────────────────────────────────

def analyze_csv(path: Path, report: EDAReport) -> None:
    import csv
    report.format_detected = "CSV/Tabular Dataset"

    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        report.errors.append("CSV file is empty.")
        return

    report.columns = list(rows[0].keys())
    report.num_rows = len(rows)
    report.num_cols = len(report.columns)

    # Missing values per column
    for col in report.columns:
        missing = sum(1 for row in rows if not row.get(col, "").strip())
        if missing:
            report.missing_values[col] = missing

    # Detect label column (common names)
    label_col = next(
        (c for c in report.columns if c.lower() in ("label", "class", "target", "y", "category")),
        None,
    )
    if label_col:
        label_counts = Counter(row[label_col].strip() for row in rows if row.get(label_col))
        report.label_distribution = dict(label_counts.most_common())

        counts = list(label_counts.values())
        if counts and max(counts) / max(min(counts), 1) > 5:
            report.warnings.append(
                f"Class imbalance in '{label_col}': "
                f"ratio {max(counts)/min(counts):.1f}:1"
            )
    else:
        report.warnings.append(
            "No standard label column found (tried: label, class, target, y, category). "
            "Verify your column names."
        )

    # Numeric stats for up to 10 columns
    if HAS_NUMPY:
        numeric_cols = []
        for col in report.columns[:20]:
            try:
                vals = [float(row[col]) for row in rows if row.get(col, "").strip()]
                if vals:
                    arr = np.array(vals)
                    report.numeric_stats[col] = {
                        "mean": float(arr.mean()),
                        "std": float(arr.std()),
                        "min": float(arr.min()),
                        "max": float(arr.max()),
                        "missing": report.missing_values.get(col, 0),
                    }
                    numeric_cols.append(col)
                if len(numeric_cols) >= 10:
                    break
            except ValueError:
                pass


# ── NumPy analysis ─────────────────────────────────────────────────────────────

def analyze_numpy(path: Path, report: EDAReport) -> None:
    if not HAS_NUMPY:
        report.errors.append("numpy not installed. Install with: pip install numpy")
        return

    report.format_detected = "NumPy Array"
    if path.suffix == ".npz":
        data = np.load(path, allow_pickle=True)
        for key in data.files:
            arr = data[key]
            report.array_shapes.append((key, arr.shape))
            report.array_dtypes.append(f"{key}: {arr.dtype}")
            if arr.dtype.kind in ("f", "i", "u"):
                report.array_stats[key] = {
                    "shape": arr.shape,
                    "dtype": str(arr.dtype),
                    "min": float(arr.min()),
                    "max": float(arr.max()),
                    "mean": float(arr.mean()),
                    "nan_count": int(np.isnan(arr).sum()) if arr.dtype.kind == "f" else 0,
                }
    else:
        arr = np.load(path, allow_pickle=True)
        report.array_shapes.append(("array", arr.shape))
        report.array_dtypes.append(str(arr.dtype))
        if arr.dtype.kind in ("f", "i", "u"):
            report.array_stats["array"] = {
                "shape": arr.shape,
                "dtype": str(arr.dtype),
                "min": float(arr.min()),
                "max": float(arr.max()),
                "mean": float(arr.mean()),
                "nan_count": int(np.isnan(arr).sum()) if arr.dtype.kind == "f" else 0,
            }


# ── HDF5 analysis ──────────────────────────────────────────────────────────────

def analyze_hdf5(path: Path, report: EDAReport) -> None:
    if not HAS_H5PY:
        report.errors.append("h5py not installed. Install with: pip install h5py")
        return

    report.format_detected = "HDF5 File"
    with h5py.File(path, "r") as f:
        def visitor(name, obj):
            if isinstance(obj, h5py.Dataset):
                report.hdf5_keys.append(name)
                report.hdf5_shapes[name] = obj.shape

        f.visititems(visitor)

    if not report.hdf5_keys:
        report.warnings.append("HDF5 file contains no datasets.")


# ── JSON annotation analysis ───────────────────────────────────────────────────

def analyze_json_annotations(path: Path, report: EDAReport) -> None:
    report.format_detected = "JSON Annotations"
    data = json.loads(path.read_text(encoding="utf-8"))

    # COCO format detection
    if isinstance(data, dict) and "annotations" in data and "categories" in data:
        categories = {c["id"]: c["name"] for c in data.get("categories", [])}
        ann_counts: Counter = Counter()
        for ann in data.get("annotations", []):
            cat_id = ann.get("category_id")
            ann_counts[categories.get(cat_id, f"id_{cat_id}")] += 1

        report.annotation_count = len(data["annotations"])
        report.annotation_classes = dict(ann_counts)

        # Images without annotations
        annotated_images = {ann["image_id"] for ann in data["annotations"]}
        total_images = len(data.get("images", []))
        report.images_without_annotations = total_images - len(annotated_images)
        if report.images_without_annotations > 0:
            pct = report.images_without_annotations / max(total_images, 1) * 100
            report.warnings.append(
                f"{report.images_without_annotations} images ({pct:.1f}%) have no annotations."
            )
        return

    # Flat label dict format: {"image.jpg": "class_name", ...}
    if isinstance(data, dict):
        counter: Counter = Counter(str(v) for v in data.values())
        report.annotation_classes = dict(counter)
        report.annotation_count = len(data)
        return

    # List of dicts: [{"image": "...", "label": "..."}, ...]
    if isinstance(data, list) and data and isinstance(data[0], dict):
        label_key = next(
            (k for k in data[0] if k.lower() in ("label", "class", "category", "target")),
            None,
        )
        if label_key:
            counter = Counter(str(item.get(label_key, "unknown")) for item in data)
            report.annotation_classes = dict(counter)
        report.annotation_count = len(data)


# ── Report generation ──────────────────────────────────────────────────────────

def generate_markdown_report(report: EDAReport) -> str:
    lines: list[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines += [
        f"# EDA Report: {report.data_path.name}",
        f"*Generated: {now} | Format: {report.format_detected}*",
        "",
        "---",
        "",
        "## A. Dataset Overview",
        "",
        f"| Property | Value |",
        f"| :--- | :--- |",
        f"| Path | `{report.data_path}` |",
        f"| Format | {report.format_detected} |",
    ]

    # Format-specific overview
    if report.classes:
        lines += [
            f"| Total Images | {report.total_images:,} |",
            f"| Number of Classes | {len(report.classes)} |",
        ]
        if report.splits_found:
            for split, count in report.splits_found.items():
                lines.append(f"| Split: {split} | {count:,} images |")
    if report.num_rows:
        lines += [
            f"| Rows | {report.num_rows:,} |",
            f"| Columns | {report.num_cols} |",
        ]

    lines += ["", "---", "", "## B. Class Distribution", ""]

    if report.classes:
        total = sum(c.count for c in report.classes) or 1
        lines += [
            "| Class | Count | % of Total |",
            "| :--- | ---: | ---: |",
        ]
        for c in sorted(report.classes, key=lambda x: -x.count):
            pct = c.count / total * 100
            bar = "█" * int(pct / 5)
            lines.append(f"| {c.name} | {c.count:,} | {pct:.1f}% {bar} |")

    elif report.label_distribution:
        total = sum(report.label_distribution.values()) or 1
        lines += [
            "| Label | Count | % of Total |",
            "| :--- | ---: | ---: |",
        ]
        for label, count in report.label_distribution.items():
            pct = count / total * 100
            lines.append(f"| {label} | {count:,} | {pct:.1f}% |")

    elif report.annotation_classes:
        lines += [
            f"Total annotations: {report.annotation_count:,}",
            "",
            "| Class | Count |",
            "| :--- | ---: |",
        ]
        for cls, count in sorted(report.annotation_classes.items(), key=lambda x: -x[1]):
            lines.append(f"| {cls} | {count:,} |")

    else:
        lines.append("*No class/label information available.*")

    lines += ["", "---", "", "## C. Data Quality Assessment", ""]

    # Image sizes
    if report.image_sizes:
        from collections import Counter as C
        size_counts = C(report.image_sizes)
        most_common_size, count = size_counts.most_common(1)[0]
        pct = count / len(report.image_sizes) * 100
        lines += [
            f"| Property | Value |",
            f"| :--- | :--- |",
            f"| Most common image size | {most_common_size[0]}×{most_common_size[1]}px ({pct:.0f}% of sample) |",
            f"| Unique sizes in sample | {len(size_counts)} |",
            f"| Corrupt/unreadable files | {len(report.corrupt_files)} |",
            "",
        ]

    # Missing values
    if report.missing_values:
        total = report.num_rows or 1
        lines += [
            "**Missing Values:**",
            "",
            "| Column | Missing | % |",
            "| :--- | ---: | ---: |",
        ]
        for col, count in sorted(report.missing_values.items(), key=lambda x: -x[1]):
            lines.append(f"| {col} | {count} | {count/total*100:.1f}% |")
        lines.append("")
    elif report.num_rows:
        lines.append("✓ No missing values detected.")
        lines.append("")

    # NumPy stats
    if report.array_stats:
        lines += ["**Array Statistics:**", ""]
        for key, stats in report.array_stats.items():
            lines += [
                f"*{key}*: shape={stats['shape']}, dtype={stats['dtype']}  ",
                f"min={stats['min']:.4f}, max={stats['max']:.4f}, mean={stats['mean']:.4f}",
                f"NaN count: {stats.get('nan_count', 0)}",
                "",
            ]

    # HDF5
    if report.hdf5_keys:
        lines += [
            "**HDF5 Datasets:**", "",
            "| Dataset | Shape |",
            "| :--- | :--- |",
        ]
        for key in report.hdf5_keys:
            lines.append(f"| {key} | {report.hdf5_shapes[key]} |")
        lines.append("")

    # Split verification
    lines += ["---", "", "## D. Split Verification", ""]
    if report.splits_found:
        total_split = sum(report.splits_found.values()) or 1
        lines += [
            "| Split | Count | % |",
            "| :--- | ---: | ---: |",
        ]
        for split, count in report.splits_found.items():
            pct = count / total_split * 100
            lines.append(f"| {split} | {count:,} | {pct:.1f}% |")

        # Check for reasonable split ratios
        counts = list(report.splits_found.values())
        if len(counts) >= 2:
            train_count = report.splits_found.get("train", counts[0])
            if train_count / total_split < 0.5:
                report.warnings.append(
                    f"Training split is only {train_count/total_split*100:.0f}% of total data. "
                    f"Typical splits: 70-80% train, 10-15% val, 10-15% test."
                )
    else:
        lines.append("⚠ No explicit split directories found.")
        lines.append(
            "Ensure you implement train/val/test splits in your DataLoader. "
            "Recommended: 70/15/15 or 80/10/10."
        )

    # Warnings and errors
    if report.warnings or report.errors:
        lines += ["", "---", "", "## E. Issues & Recommendations", ""]
        for w in report.warnings:
            lines.append(f"⚠ **Warning:** {w}")
        for e in report.errors:
            lines.append(f"✗ **Error:** {e}")
        lines.append("")

    lines += [
        "---",
        "",
        "## F. EDA Summary for TSK-001",
        "",
        "| Check | Status |",
        "| :--- | :--- |",
        f"| Class distribution analyzed | {'✓' if report.classes or report.label_distribution or report.annotation_classes else '✗'} |",
        f"| Missing/corrupt data checked | {'✓' if not report.errors else '⚠'} |",
        f"| Class imbalance assessed | {'✓' if report.classes or report.label_distribution else 'N/A'} |",
        f"| Split structure verified | {'✓' if report.splits_found else '⚠ manual check needed'} |",
        f"| Issues found | {len(report.warnings)} warning(s), {len(report.errors)} error(s) |",
        "",
        "*Complete this EDA before proceeding to TSK-002 (DataLoader implementation).*",
    ]

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def analyze(data_path: Path, split_names: list[str] | None = None) -> EDAReport:
    split_names = split_names or ["train", "val", "test", "validation"]
    report = EDAReport(data_path=data_path, format_detected="unknown")
    fmt = detect_format(data_path)

    if fmt == "image_dir":
        analyze_image_dir(data_path, report, split_names)
    elif fmt == "csv":
        analyze_csv(data_path, report)
    elif fmt == "numpy":
        analyze_numpy(data_path, report)
    elif fmt == "hdf5":
        analyze_hdf5(data_path, report)
    elif fmt == "json_annotations":
        analyze_json_annotations(data_path, report)
    else:
        report.errors.append(
            f"Unrecognized format for '{data_path}'. "
            f"Supported: image directory, CSV, .npy/.npz, .h5/.hdf5, .json (annotations)"
        )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="ML EDA Analyzer for BMAD DL Lifecycle")
    parser.add_argument("data_path", type=Path, help="Path to dataset file or directory")
    parser.add_argument("--output", type=Path, default=None,
                        help="Output markdown report path (default: <data_path>_eda_report.md)")
    parser.add_argument("--splits", nargs="+", default=["train", "val", "test"],
                        help="Expected split directory names")
    args = parser.parse_args()

    if not args.data_path.exists():
        print(f"Error: Path not found: {args.data_path}", file=sys.stderr)
        return 2

    report = analyze(args.data_path, args.splits)
    markdown = generate_markdown_report(report)

    output_path = args.output or args.data_path.parent / f"{args.data_path.stem}_eda_report.md"
    output_path.write_text(markdown, encoding="utf-8")

    print(f"\n✓ EDA report written to: {output_path}")
    print(f"  Format: {report.format_detected}")
    if report.classes:
        print(f"  Classes: {len(report.classes)}, Total samples: {report.total_images:,}")
    if report.warnings:
        print(f"  ⚠ {len(report.warnings)} warning(s) — review report for details")
    if report.errors:
        print(f"  ✗ {len(report.errors)} error(s)")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
