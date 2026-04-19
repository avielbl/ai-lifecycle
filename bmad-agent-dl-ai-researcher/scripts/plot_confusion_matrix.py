#!/usr/bin/env python3
"""
plot_confusion_matrix.py — BMAD DL Lifecycle
(Inspired by K-Dense matplotlib/plot_template.py + scikit-learn/classification_pipeline.py)

Generates confusion matrix plot, per-class metric bar chart, and classification
report from model predictions. Designed for use in Phase 5 (Analysis).

Inputs:
  - A predictions CSV with columns: y_true, y_pred (and optional y_score for ROC)
  - OR two separate text files: ground truth labels, predicted labels (one per line)

Outputs:
  - confusion_matrix.png   — normalized + raw count heatmap
  - per_class_metrics.png  — precision/recall/F1 per class bar chart
  - Markdown text block for pasting into the analysis document

Usage:
    python3 scripts/plot_confusion_matrix.py <predictions_csv> [--output-dir outputs/]
    python3 scripts/plot_confusion_matrix.py predictions.csv --true-col label --pred-col prediction
    python3 scripts/plot_confusion_matrix.py --true-file gt.txt --pred-file preds.txt

Exit codes:
    0 — success
    2 — error
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    from sklearn.metrics import (
        confusion_matrix, classification_report,
        precision_score, recall_score, f1_score, accuracy_score,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ── Data loading ───────────────────────────────────────────────────────────────

def load_predictions_csv(
    path: Path, true_col: str, pred_col: str
) -> tuple[list[str], list[str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("Empty predictions file")

    columns = list(rows[0].keys())

    # Auto-detect column names if not specified
    if true_col not in columns:
        candidates = [c for c in columns if c.lower() in ("y_true", "true", "label", "actual", "ground_truth")]
        if not candidates:
            raise ValueError(f"True label column '{true_col}' not found. Available: {columns}")
        true_col = candidates[0]

    if pred_col not in columns:
        candidates = [c for c in columns if c.lower() in ("y_pred", "pred", "predicted", "prediction")]
        if not candidates:
            raise ValueError(f"Prediction column '{pred_col}' not found. Available: {columns}")
        pred_col = candidates[0]

    y_true = [row[true_col].strip() for row in rows]
    y_pred = [row[pred_col].strip() for row in rows]
    return y_true, y_pred


def load_label_files(true_file: Path, pred_file: Path) -> tuple[list[str], list[str]]:
    y_true = [line.strip() for line in true_file.read_text().splitlines() if line.strip()]
    y_pred = [line.strip() for line in pred_file.read_text().splitlines() if line.strip()]
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: {len(y_true)} true vs {len(y_pred)} predicted")
    return y_true, y_pred


# ── Plotting ───────────────────────────────────────────────────────────────────

def plot_confusion_matrix(
    y_true: list[str], y_pred: list[str], class_names: list[str], output_path: Path
) -> None:
    cm = confusion_matrix(y_true, y_pred, labels=class_names)
    cm_norm = cm.astype(float) / cm.sum(axis=1, keepdims=True).clip(min=1)

    n = len(class_names)
    cell_size = max(0.7, min(1.2, 8.0 / n))
    fig_size = max(6, n * cell_size + 2)

    fig, axes = plt.subplots(1, 2, figsize=(fig_size * 2 + 1, fig_size), constrained_layout=True)

    for ax, (data, title, fmt) in zip(axes, [
        (cm_norm, "Normalized Confusion Matrix", ".2f"),
        (cm, "Raw Count Confusion Matrix", "d"),
    ]):
        cmap = "Blues"
        im = ax.imshow(data, interpolation="nearest", cmap=cmap,
                       vmin=0, vmax=(1.0 if "Normalized" in title else None))

        thresh = (data.max() + data.min()) / 2.0
        for i in range(n):
            for j in range(n):
                val = data[i, j]
                text = f"{val:{fmt}}" if fmt == "d" else f"{val:.2f}"
                color = "white" if val > thresh else "black"
                ax.text(j, i, text, ha="center", va="center",
                        color=color, fontsize=max(5, min(10, 90 // n)))

        ax.set_xlabel("Predicted", fontsize=11)
        ax.set_ylabel("True", fontsize=11)
        ax.set_title(title, fontsize=12, pad=10)
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(class_names, rotation=45, ha="right",
                           fontsize=max(6, min(10, 80 // n)))
        ax.set_yticklabels(class_names, fontsize=max(6, min(10, 80 // n)))
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    fig.suptitle("Confusion Matrix Analysis", fontsize=14, fontweight="bold")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


def plot_per_class_metrics(
    y_true: list[str], y_pred: list[str], class_names: list[str], output_path: Path
) -> None:
    precision = precision_score(y_true, y_pred, labels=class_names,
                                average=None, zero_division=0)
    recall = recall_score(y_true, y_pred, labels=class_names,
                          average=None, zero_division=0)
    f1 = f1_score(y_true, y_pred, labels=class_names, average=None, zero_division=0)

    x = range(len(class_names))
    width = 0.25

    fig_w = max(8, len(class_names) * 0.9 + 2)
    fig, ax = plt.subplots(figsize=(fig_w, 5), constrained_layout=True)

    bars_p = ax.bar([i - width for i in x], precision, width,
                    label="Precision", color="#2196F3", alpha=0.85, edgecolor="white")
    bars_r = ax.bar(x, recall, width,
                    label="Recall", color="#4CAF50", alpha=0.85, edgecolor="white")
    bars_f = ax.bar([i + width for i in x], f1, width,
                    label="F1-Score", color="#F44336", alpha=0.85, edgecolor="white")

    # Value labels on bars
    for bars in (bars_p, bars_r, bars_f):
        for bar in bars:
            h = bar.get_height()
            if h > 0.02:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.01,
                        f"{h:.2f}", ha="center", va="bottom",
                        fontsize=max(6, min(8, 60 // len(class_names))))

    ax.set_xlabel("Class", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title("Per-Class Metrics", fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, rotation=30, ha="right",
                       fontsize=max(7, min(10, 80 // len(class_names))))
    ax.set_ylim(0, 1.12)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Weighted averages as text box
    w_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    w_prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    w_rec = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    acc = accuracy_score(y_true, y_pred)
    summary = f"Accuracy: {acc:.4f}  |  W-F1: {w_f1:.4f}  |  W-Prec: {w_prec:.4f}  |  W-Rec: {w_rec:.4f}"
    ax.text(0.5, 1.04, summary, transform=ax.transAxes, ha="center",
            fontsize=9, style="italic",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))

    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {output_path}")


# ── Markdown report ────────────────────────────────────────────────────────────

def generate_markdown(
    y_true: list[str], y_pred: list[str], class_names: list[str],
    cm_path: Path | None, metrics_path: Path | None,
) -> str:
    acc = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, labels=class_names,
                                   zero_division=0, output_dict=True)
    lines: list[str] = [
        "## Prediction Analysis",
        "",
        f"**Overall Accuracy:** {acc:.4f}",
        "",
        "### Per-Class Metrics",
        "",
        "| Class | Precision | Recall | F1-Score | Support |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for cls in class_names:
        r = report.get(cls, {})
        lines.append(
            f"| {cls} | {r.get('precision', 0):.4f} | {r.get('recall', 0):.4f} | "
            f"{r.get('f1-score', 0):.4f} | {int(r.get('support', 0))} |"
        )

    wa = report.get("weighted avg", {})
    lines += [
        f"| **Weighted Avg** | **{wa.get('precision', 0):.4f}** | **{wa.get('recall', 0):.4f}** | "
        f"**{wa.get('f1-score', 0):.4f}** | **{int(wa.get('support', 0))}** |",
        "",
    ]

    if cm_path:
        lines += [f"![Confusion Matrix]({cm_path.name})", ""]
    if metrics_path:
        lines += [f"![Per-Class Metrics]({metrics_path.name})", ""]

    lines += [
        "### Classification Report",
        "```",
        classification_report(y_true, y_pred, labels=class_names,
                               target_names=class_names, zero_division=0),
        "```",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Plot confusion matrix and per-class metrics")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("predictions_csv", type=Path, nargs="?", default=None)
    group.add_argument("--true-file", type=Path)
    parser.add_argument("--pred-file", type=Path)
    parser.add_argument("--true-col", type=str, default="y_true")
    parser.add_argument("--pred-col", type=str, default="y_pred")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    if not HAS_MPL or not HAS_SKLEARN:
        missing = []
        if not HAS_MPL:
            missing.append("matplotlib numpy")
        if not HAS_SKLEARN:
            missing.append("scikit-learn")
        print(f"Error: Missing dependencies: pip install {' '.join(missing)}", file=sys.stderr)
        return 2

    # Load data
    try:
        if args.predictions_csv:
            if not args.predictions_csv.exists():
                print(f"Error: File not found: {args.predictions_csv}", file=sys.stderr)
                return 2
            y_true, y_pred = load_predictions_csv(
                args.predictions_csv, args.true_col, args.pred_col
            )
            out_dir = args.output_dir or args.predictions_csv.parent
            stem = args.predictions_csv.stem
        else:
            if not args.true_file or not args.pred_file:
                print("Error: --true-file and --pred-file both required", file=sys.stderr)
                return 2
            y_true, y_pred = load_label_files(args.true_file, args.pred_file)
            out_dir = args.output_dir or args.true_file.parent
            stem = args.true_file.stem
    except Exception as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    class_names = sorted(set(y_true) | set(y_pred))
    n = len(y_true)
    print(f"Predictions: {n} samples, {len(class_names)} classes: {class_names}")

    cm_path = out_dir / f"{stem}_confusion_matrix.png"
    metrics_path = out_dir / f"{stem}_per_class_metrics.png"
    md_path = out_dir / f"{stem}_analysis.md"

    plot_confusion_matrix(y_true, y_pred, class_names, cm_path)
    plot_per_class_metrics(y_true, y_pred, class_names, metrics_path)

    md = generate_markdown(y_true, y_pred, class_names, cm_path, metrics_path)
    md_path.write_text(md, encoding="utf-8")
    print(f"  Saved: {md_path}")

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    print(f"\n✓ Accuracy: {acc:.4f}  |  Weighted F1: {f1:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
