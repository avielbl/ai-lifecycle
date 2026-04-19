#!/usr/bin/env python3
"""
class_weights_calculator.py — BMAD DL Lifecycle
Computes class weights for imbalanced datasets to use in weighted loss functions.

Supports:
  - Image datasets (class-labeled subdirectory layout)
  - CSV/TSV tabular datasets
  - JSON annotation files (COCO or flat dict)

Outputs ready-to-paste Python dict for PyTorch loss functions, plus a
markdown summary. Works entirely with stdlib (no external deps).

Usage:
    python3 scripts/class_weights_calculator.py <data_path> [--label-col LABEL] [--output report.md]
    python3 scripts/class_weights_calculator.py data/images/      # image dir
    python3 scripts/class_weights_calculator.py data/labels.csv --label-col defective
    python3 scripts/class_weights_calculator.py data/annotations.json

Exit codes:
    0 — success
    2 — error
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def count_image_classes(data_dir: Path) -> dict[str, int]:
    """Count images per class from class-labeled subdirectories."""
    counts: dict[str, int] = {}
    subdirs = [d for d in sorted(data_dir.iterdir()) if d.is_dir()]
    if not subdirs:
        raise ValueError(f"No subdirectories found in {data_dir}. "
                         "Expected class-labeled subdirectory layout: data/class_name/img.jpg")
    for cls_dir in subdirs:
        images = [f for f in cls_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
        if images:
            counts[cls_dir.name] = len(images)
    return counts


def count_csv_classes(path: Path, label_col: str | None) -> dict[str, int]:
    """Count class frequencies from a CSV label column."""
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("CSV is empty")

    columns = list(rows[0].keys())
    if label_col and label_col in columns:
        target = label_col
    else:
        target = next(
            (c for c in columns if c.lower() in ("label", "class", "target", "y", "category")),
            None,
        )
    if target is None:
        raise ValueError(
            f"No label column found. Use --label-col or name your column: "
            f"label, class, target, y, category"
        )
    counter = Counter(row[target].strip() for row in rows if row.get(target, "").strip())
    return dict(counter)


def count_json_classes(path: Path) -> dict[str, int]:
    """Count class frequencies from JSON annotations (COCO or flat dict)."""
    data = json.loads(path.read_text(encoding="utf-8"))

    # COCO format
    if isinstance(data, dict) and "annotations" in data and "categories" in data:
        categories = {c["id"]: c["name"] for c in data.get("categories", [])}
        counter: Counter = Counter()
        for ann in data.get("annotations", []):
            cat_id = ann.get("category_id")
            counter[categories.get(cat_id, f"id_{cat_id}")] += 1
        return dict(counter)

    # Flat dict: {"img.jpg": "class_name"}
    if isinstance(data, dict):
        return dict(Counter(str(v) for v in data.values()))

    # List of dicts
    if isinstance(data, list) and data and isinstance(data[0], dict):
        label_key = next(
            (k for k in data[0] if k.lower() in ("label", "class", "category", "target")),
            None,
        )
        if label_key:
            return dict(Counter(str(item.get(label_key, "unknown")) for item in data))

    raise ValueError("Unrecognized JSON annotation format")


def compute_weights(counts: dict[str, int]) -> dict[str, float]:
    """
    Compute balanced class weights: weight_i = n_samples / (n_classes * count_i).
    This is sklearn's 'balanced' strategy, equivalent to:
        sklearn.utils.class_weight.compute_class_weight('balanced', ...)
    """
    n_samples = sum(counts.values())
    n_classes = len(counts)
    return {
        cls: round(n_samples / (n_classes * count), 6)
        for cls, count in counts.items()
    }


def compute_inverse_freq_weights(counts: dict[str, int]) -> dict[str, float]:
    """Normalized inverse frequency weights: weight_i = (1/count_i) / sum(1/count_j)."""
    inv = {cls: 1.0 / count for cls, count in counts.items()}
    total_inv = sum(inv.values())
    return {cls: round(v / total_inv, 6) for cls, v in inv.items()}


def generate_report(
    counts: dict[str, int],
    weights_balanced: dict[str, float],
    weights_inv: dict[str, float],
    data_path: Path,
) -> str:
    total = sum(counts.values())
    n_classes = len(counts)
    sorted_classes = sorted(counts, key=lambda c: -counts[c])

    lines: list[str] = [
        "# Class Weights Report",
        f"*Dataset: `{data_path.name}` | {total:,} samples | {n_classes} classes*",
        "",
        "---",
        "",
        "## A. Class Distribution",
        "",
        "| Class | Count | % | Imbalance Ratio |",
        "| :--- | ---: | ---: | ---: |",
    ]
    majority = counts[sorted_classes[0]]
    for cls in sorted_classes:
        pct = counts[cls] / total * 100
        ratio = majority / counts[cls]
        bar = "█" * int(pct / 5)
        lines.append(f"| {cls} | {counts[cls]:,} | {pct:.1f}% {bar} | {ratio:.1f}:1 |")

    max_ratio = majority / counts[sorted_classes[-1]]
    if max_ratio > 10:
        lines += ["", f"⚠ **Severe imbalance** detected: {max_ratio:.0f}:1 ratio. Weighted loss is strongly recommended."]
    elif max_ratio > 3:
        lines += ["", f"⚠ **Moderate imbalance** detected: {max_ratio:.0f}:1 ratio. Consider weighted loss."]
    else:
        lines += ["", f"✓ Dataset is relatively balanced ({max_ratio:.1f}:1 ratio)."]

    # Balanced weights
    sorted_by_cls = sorted(weights_balanced)
    lines += [
        "",
        "---",
        "",
        "## B. Balanced Class Weights",
        "",
        "*Formula: `n_samples / (n_classes × class_count)` — equivalent to sklearn's `class_weight='balanced'`*",
        "",
        "| Class | Count | Weight |",
        "| :--- | ---: | ---: |",
    ]
    for cls in sorted_by_cls:
        lines.append(f"| {cls} | {counts[cls]:,} | {weights_balanced[cls]:.4f} |")

    # Python code snippets
    weight_list_balanced = [weights_balanced[c] for c in sorted(weights_balanced)]
    lines += [
        "",
        "### PyTorch Usage",
        "",
        "```python",
        "import torch",
        "",
        "# Option 1: As tensor for nn.CrossEntropyLoss",
        f"class_names = {sorted_by_cls}",
        f"weights = torch.tensor({[round(weights_balanced[c], 4) for c in sorted_by_cls]}, dtype=torch.float)",
        "criterion = torch.nn.CrossEntropyLoss(weight=weights.to(device))",
        "",
        "# Option 2: As dict (for custom loss or WeightedRandomSampler)",
        f"class_weight_dict = {dict(zip(sorted_by_cls, [weights_balanced[c] for c in sorted_by_cls]))}",
        "```",
        "",
    ]

    # Inverse freq weights
    lines += [
        "---",
        "",
        "## C. Inverse Frequency Weights (Normalized)",
        "",
        "*Alternative: normalized so weights sum to 1.0*",
        "",
        "| Class | Count | Weight |",
        "| :--- | ---: | ---: |",
    ]
    for cls in sorted_by_cls:
        lines.append(f"| {cls} | {counts[cls]:,} | {weights_inv[cls]:.4f} |")

    lines += [
        "",
        "```python",
        "# Inverse frequency weights tensor",
        f"weights_inv = torch.tensor({[round(weights_inv[c], 4) for c in sorted_by_cls]}, dtype=torch.float)",
        "```",
        "",
        "---",
        "",
        "## D. Recommendations",
        "",
    ]
    if max_ratio > 10:
        lines += [
            "1. Use `CrossEntropyLoss(weight=...)` with balanced weights (Section B).",
            "2. Consider `WeightedRandomSampler` to oversample minority classes in each batch.",
            "3. Use per-class metrics (F1, precision, recall per class) — not just accuracy.",
            "4. Consider Focal Loss for severe imbalance (set `gamma=2`).",
        ]
    elif max_ratio > 3:
        lines += [
            "1. Apply balanced class weights to your loss function (Section B).",
            "2. Monitor per-class F1 during training.",
            "3. Consider data augmentation on minority classes.",
        ]
    else:
        lines += [
            "1. Dataset is balanced — standard `CrossEntropyLoss` without weights is acceptable.",
            "2. Monitor per-class metrics to catch any per-class degradation.",
        ]

    lines += [
        "",
        "---",
        "*Generated by `class_weights_calculator.py` — BMAD DL Lifecycle*",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute class weights for imbalanced datasets")
    parser.add_argument("data_path", type=Path)
    parser.add_argument("--label-col", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    if not args.data_path.exists():
        print(f"Error: Path not found: {args.data_path}", file=sys.stderr)
        return 2

    try:
        if args.data_path.is_dir():
            counts = count_image_classes(args.data_path)
        elif args.data_path.suffix.lower() in (".csv", ".tsv"):
            counts = count_csv_classes(args.data_path, args.label_col)
        elif args.data_path.suffix.lower() == ".json":
            counts = count_json_classes(args.data_path)
        else:
            print(f"Error: Unsupported format. Use image dir, CSV, or JSON.", file=sys.stderr)
            return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if not counts:
        print("Error: No class data found.", file=sys.stderr)
        return 2

    weights_balanced = compute_weights(counts)
    weights_inv = compute_inverse_freq_weights(counts)

    report = generate_report(counts, weights_balanced, weights_inv, args.data_path)

    output = args.output or args.data_path.parent / f"{args.data_path.stem}_class_weights.md"
    output.write_text(report, encoding="utf-8")

    print(f"✓ Class weight report: {output}")
    print(f"  Classes: {list(counts.keys())}")
    print(f"  Balanced weights: {weights_balanced}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
