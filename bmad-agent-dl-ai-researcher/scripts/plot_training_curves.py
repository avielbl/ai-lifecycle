#!/usr/bin/env python3
"""
plot_training_curves.py — BMAD DL Lifecycle
(Inspired by K-Dense matplotlib/plot_template.py)

Generates publication-quality training curve plots from CSV metric logs.
Reads Lightning CSVLogger format (one metric per row) or flat per-epoch CSVs.

Produces:
  - Loss curves (train + val on same axes)
  - Per-metric curves (F1, accuracy, AUC, etc.) on separate subplots
  - Annotated best-epoch marker
  - Saved as PNG (and optional SVG)

Usage:
    python3 scripts/plot_training_curves.py <metrics_csv> [--output curves.png] [--metrics f1 acc]
    python3 scripts/plot_training_curves.py logs/run_001/version_0/metrics.csv

Exit codes:
    0 — success
    2 — error
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


# ── Data loading ───────────────────────────────────────────────────────────────

def _try_float(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_metrics(path: Path) -> dict[str, list[float]]:
    """
    Load a Lightning-style metrics.csv (one metric per row, others empty)
    or a flat per-epoch CSV (one row per epoch).

    Returns {metric_name: [value_per_epoch_or_step]}.
    """
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("Empty metrics file")

    # Detect Lightning sparse format (most values are empty per row)
    non_empty_per_row = [
        sum(1 for v in row.values() if v.strip() not in ("", "nan", "NaN"))
        for row in rows
    ]
    avg_non_empty = sum(non_empty_per_row) / len(non_empty_per_row)
    is_sparse = avg_non_empty < 4  # Lightning typically has 2-3 non-empty per row

    columns = list(rows[0].keys())

    if is_sparse:
        return _load_sparse(rows, columns)
    else:
        return _load_flat(rows, columns)


def _load_sparse(rows: list[dict], columns: list[str]) -> dict[str, list[float]]:
    """Lightning CSVLogger: aggregate rows by epoch, take last value per epoch per metric."""
    epoch_data: dict[int, dict[str, float]] = defaultdict(dict)
    for row in rows:
        epoch_str = row.get("epoch", "").strip()
        epoch = int(float(epoch_str)) if epoch_str and epoch_str not in ("", "nan") else None
        if epoch is None:
            continue
        for col, val in row.items():
            if col in ("epoch", "step"):
                continue
            v = _try_float(val)
            if v is not None:
                epoch_data[epoch][col] = v

    if not epoch_data:
        raise ValueError("No epoch data found in sparse CSV")

    metrics: dict[str, list[float]] = defaultdict(list)
    for epoch in sorted(epoch_data):
        for col, v in epoch_data[epoch].items():
            metrics[col].append(v)

    # Pad shorter lists with NaN for alignment
    max_len = max(len(v) for v in metrics.values()) if metrics else 0
    for key in metrics:
        while len(metrics[key]) < max_len:
            metrics[key].append(float("nan"))

    return dict(metrics)


def _load_flat(rows: list[dict], columns: list[str]) -> dict[str, list[float]]:
    """Flat per-epoch CSV: one row per epoch."""
    metrics: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        for col in columns:
            if col in ("epoch", "step"):
                continue
            v = _try_float(row.get(col, ""))
            if v is not None:
                metrics[col].append(v)
    return dict(metrics)


# ── Curve grouping ─────────────────────────────────────────────────────────────

def group_metrics(metrics: dict[str, list[float]]) -> dict[str, dict[str, list[float]]]:
    """
    Group metrics into logical panels:
      'loss'  → train_loss, val_loss, train/loss, val/loss
      'other' → per remaining metric
    """
    groups: dict[str, dict[str, list[float]]] = {"loss": {}}
    loss_keywords = ("loss",)

    for name, values in metrics.items():
        if any(kw in name.lower() for kw in loss_keywords):
            groups["loss"][name] = values
        else:
            # Each non-loss metric gets its own panel, but pair train/val variants
            base = name.replace("train/", "").replace("val/", "").replace("train_", "").replace("val_", "")
            groups.setdefault(base, {})[name] = values

    # Remove empty loss group
    if not groups["loss"]:
        del groups["loss"]

    return groups


# ── Plotting ───────────────────────────────────────────────────────────────────

_TRAIN_COLORS = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]
_VAL_COLORS = ["#F44336", "#009688", "#E91E63", "#FF5722"]
_LINESTYLES = ["-", "--", "-.", ":"]


def _is_train(name: str) -> bool:
    return "train" in name.lower() and "val" not in name.lower()


def _best_epoch(values: list[float], mode: str = "min") -> int | None:
    """Index of best value, ignoring NaN."""
    valid = [(i, v) for i, v in enumerate(values) if v == v]  # filter nan
    if not valid:
        return None
    return min(valid, key=lambda x: x[1] if mode == "min" else -x[1])[0]


def plot_curves(
    metrics: dict[str, list[float]],
    title: str,
    output_path: Path,
    extra_metric_names: list[str] | None = None,
) -> None:
    groups = group_metrics(metrics)

    # Filter to requested metrics if specified
    if extra_metric_names:
        filtered: dict[str, dict[str, list[float]]] = {}
        if "loss" in groups:
            filtered["loss"] = groups["loss"]
        for key, vals in groups.items():
            if key == "loss":
                continue
            if any(m.lower() in key.lower() for m in extra_metric_names):
                filtered[key] = vals
        if filtered:
            groups = filtered

    n_panels = len(groups)
    if n_panels == 0:
        raise ValueError("No plottable metrics found")

    fig, axes = plt.subplots(
        1, n_panels, figsize=(max(6, 5 * n_panels), 5),
        squeeze=False, constrained_layout=True,
    )
    axes = axes[0]

    plt.rcParams.update({
        "font.size": 10, "axes.labelsize": 11, "axes.titlesize": 12,
        "lines.linewidth": 2, "axes.linewidth": 1.2,
    })

    for ax, (panel_name, panel_metrics) in zip(axes, groups.items()):
        train_idx = val_idx = 0

        for line_name, values in panel_metrics.items():
            epochs = list(range(len(values)))
            is_t = _is_train(line_name)

            if is_t:
                color = _TRAIN_COLORS[train_idx % len(_TRAIN_COLORS)]
                ls = _LINESTYLES[train_idx % len(_LINESTYLES)]
                train_idx += 1
            else:
                color = _VAL_COLORS[val_idx % len(_VAL_COLORS)]
                ls = _LINESTYLES[val_idx % len(_LINESTYLES)]
                val_idx += 1

            ax.plot(epochs, values, color=color, linestyle=ls, label=line_name, alpha=0.9)

            # Mark best val epoch for val metrics
            if not is_t and "val" in line_name.lower():
                mode = "min" if "loss" in line_name.lower() else "max"
                best_idx = _best_epoch(values, mode)
                if best_idx is not None:
                    ax.axvline(best_idx, color=color, linestyle=":", alpha=0.4, linewidth=1)
                    ax.scatter([best_idx], [values[best_idx]], color=color, s=60, zorder=5)
                    ax.annotate(
                        f"best\n{values[best_idx]:.4f}",
                        (best_idx, values[best_idx]),
                        textcoords="offset points", xytext=(6, -14),
                        fontsize=7, color=color,
                    )

        ax.set_xlabel("Epoch")
        ylabel = panel_name.replace("_", " ").replace("/", " / ").title()
        ax.set_ylabel(ylabel)
        ax.set_title(f"{ylabel} Curves")
        ax.legend(loc="best", fontsize=8, framealpha=0.8)
        ax.grid(True, alpha=0.25, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    fig.suptitle(title, fontsize=13, fontweight="bold")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Plot training curves from metrics CSV")
    parser.add_argument("metrics_csv", type=Path)
    parser.add_argument("--output", type=Path, default=None, help="Output PNG path")
    parser.add_argument("--metrics", nargs="+", default=None,
                        help="Metric names to include (default: all). E.g.: f1 acc")
    parser.add_argument("--title", type=str, default=None)
    args = parser.parse_args()

    if not HAS_MPL:
        print("Error: matplotlib not installed. Run: pip install matplotlib", file=sys.stderr)
        return 2
    if not args.metrics_csv.exists():
        print(f"Error: File not found: {args.metrics_csv}", file=sys.stderr)
        return 2

    try:
        metrics = load_metrics(args.metrics_csv)
    except Exception as e:
        print(f"Error loading metrics: {e}", file=sys.stderr)
        return 2

    if not metrics:
        print("Error: No plottable metrics found in file", file=sys.stderr)
        return 2

    print(f"Loaded metrics: {list(metrics.keys())}")
    print(f"Epochs/steps: {max(len(v) for v in metrics.values())}")

    title = args.title or f"Training Curves — {args.metrics_csv.stem}"
    output = args.output or args.metrics_csv.parent / f"{args.metrics_csv.stem}_curves.png"

    try:
        plot_curves(metrics, title, output, args.metrics)
    except Exception as e:
        print(f"Error plotting: {e}", file=sys.stderr)
        return 2

    print(f"✓ Training curves saved to: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
