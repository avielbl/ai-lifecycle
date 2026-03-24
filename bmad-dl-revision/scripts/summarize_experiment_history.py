#!/usr/bin/env python3
"""
summarize_experiment_history.py — BMAD DL Lifecycle
Scans a logs/ directory for completed experiment runs and produces a
ranked comparison table for the revision/retrospective phase.

Reads CSV metric logs produced by Lightning's CSVLogger
  (logs/<experiment>/version_N/metrics.csv)
or any CSV/JSON files matching the run structure in docs/experiments/.

Output: compact markdown table sorted by best val_loss (or configurable metric),
        ready to paste into the revision document or feed to the analysis agent.

Usage:
    python3 scripts/summarize_experiment_history.py <logs_dir> [--metric val/loss] [--top N]
    python3 scripts/summarize_experiment_history.py logs/ --metric val/f1 --top 5 --mode max
    python3 scripts/summarize_experiment_history.py docs/experiments/

Exit codes:
    0 — success
    1 — no runs found
    2 — path error
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class RunSummary:
    name: str                        # experiment/run name
    source_file: Path
    epochs: int = 0
    best_val_loss: float | None = None
    final_val_loss: float | None = None
    best_metric_value: float | None = None
    best_metric_name: str | None = None
    best_epoch: int | None = None
    all_metrics: dict[str, float] = field(default_factory=dict)
    notes: str = ""


# ── CSV parsing ────────────────────────────────────────────────────────────────

def _try_float(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _parse_metrics_csv(path: Path) -> list[dict[str, float | None]]:
    """Parse a Lightning-style metrics.csv (or any epoch-keyed CSV) into rows."""
    rows: list[dict[str, float | None]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed = {k.strip().lower(): _try_float(v) for k, v in row.items()}
            rows.append(parsed)
    return rows


def _aggregate_lightning_metrics(rows: list[dict[str, float | None]]) -> dict[str, list[float]]:
    """
    Lightning CSVLogger writes one metric per row with NaN for others.
    Aggregate into per-metric value lists, ignoring NaN rows.
    """
    aggregated: dict[str, list[float]] = {}
    for row in rows:
        for k, v in row.items():
            if v is not None and k not in ("epoch", "step"):
                aggregated.setdefault(k, []).append(v)
    return aggregated


def _best_value(values: list[float], mode: str) -> float:
    return min(values) if mode == "min" else max(values)


# ── Run discovery ─────────────────────────────────────────────────────────────

def discover_runs(logs_dir: Path) -> list[Path]:
    """
    Finds metric CSV/JSON files across common logging layouts:
      - logs/<name>/version_N/metrics.csv    (Lightning CSVLogger)
      - logs/<name>/metrics.csv              (flat layout)
      - docs/experiments/<name>_metrics.csv  (BMAD docs convention)
      - docs/experiments/<name>_metrics.json
    """
    patterns = [
        "*/version_*/metrics.csv",
        "*/metrics.csv",
        "*_metrics.csv",
        "*_metrics.json",
        "*/metrics.json",
    ]
    found: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for p in sorted(logs_dir.glob(pattern)):
            if p not in seen:
                found.append(p)
                seen.add(p)
    return found


def _run_name_from_path(p: Path, logs_dir: Path) -> str:
    """Derive a human-readable run name from the file path."""
    try:
        rel = p.relative_to(logs_dir)
    except ValueError:
        rel = p
    parts = rel.parts
    # Drop version suffix if present
    filtered = [pt for pt in parts if not pt.startswith("version_") and pt != "metrics.csv"
                and pt != "metrics.json"]
    return "/".join(filtered) if filtered else rel.stem


# ── Summary extraction ────────────────────────────────────────────────────────

def extract_run_summary(
    path: Path,
    logs_dir: Path,
    target_metric: str,
    mode: str,
) -> RunSummary | None:
    name = _run_name_from_path(path, logs_dir)
    summary = RunSummary(name=name, source_file=path)

    # Load data
    try:
        if path.suffix == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "history" in raw:
                raw = raw["history"]
            if not isinstance(raw, list):
                return None
            rows = [{k.lower(): _try_float(v) for k, v in entry.items()} for entry in raw]
        else:
            rows = _parse_metrics_csv(path)
    except Exception as e:
        summary.notes = f"parse error: {e}"
        return summary

    if not rows:
        summary.notes = "empty file"
        return None

    agg = _aggregate_lightning_metrics(rows)
    if not agg:
        return None

    # Determine total epochs
    epoch_vals = agg.get("epoch", [])
    summary.epochs = int(max(epoch_vals)) + 1 if epoch_vals else len(rows)

    # Val loss
    for vl_key in ("val/loss", "val_loss", "validation_loss"):
        if vl_key in agg and agg[vl_key]:
            vals = agg[vl_key]
            summary.best_val_loss = min(vals)
            summary.final_val_loss = vals[-1]
            if epoch_vals and len(epoch_vals) == len(vals):
                summary.best_epoch = int(epoch_vals[vals.index(summary.best_val_loss)])
            break

    # Target metric
    norm_target = target_metric.lower().replace("/", "_").replace(" ", "_")
    for k, vals in agg.items():
        norm_k = k.lower().replace("/", "_").replace(" ", "_")
        if norm_k == norm_target or norm_target in norm_k:
            summary.best_metric_value = _best_value(vals, mode)
            summary.best_metric_name = k
            break

    # Collect best values for all tracked metrics
    for k, vals in agg.items():
        if k not in ("epoch", "step"):
            m = "min" if any(lk in k.lower() for lk in ("loss", "error", "mae", "mse")) else "max"
            summary.all_metrics[k] = _best_value(vals, m)

    return summary


# ── Report generation ─────────────────────────────────────────────────────────

def generate_summary_table(
    summaries: list[RunSummary],
    target_metric: str,
    mode: str,
    top_n: int | None = None,
) -> str:
    if not summaries:
        return "_No experiment runs found._\n"

    # Sort: by target metric if available, else by val_loss
    def sort_key(s: RunSummary):
        if s.best_metric_value is not None:
            return s.best_metric_value if mode == "max" else -s.best_metric_value
        if s.best_val_loss is not None:
            return -s.best_val_loss  # lower val_loss = better
        return float("-inf")

    sorted_runs = sorted(summaries, key=sort_key, reverse=True)
    if top_n:
        sorted_runs = sorted_runs[:top_n]

    lines: list[str] = [
        "## Experiment History Summary",
        "",
        f"*Sorted by `{target_metric}` ({mode}) — top {len(sorted_runs)} of {len(summaries)} runs*",
        "",
        "| Rank | Run | Epochs | Best Val Loss | Best " + target_metric + " | Best Epoch | Notes |",
        "| ---: | :--- | ---: | ---: | ---: | ---: | :--- |",
    ]

    for rank, s in enumerate(sorted_runs, 1):
        val_loss_str = f"{s.best_val_loss:.4f}" if s.best_val_loss is not None else "—"
        metric_str = f"{s.best_metric_value:.4f}" if s.best_metric_value is not None else "—"
        epoch_str = str(s.best_epoch) if s.best_epoch is not None else "—"
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
        lines.append(
            f"| {medal} | `{s.name}` | {s.epochs} | {val_loss_str} | {metric_str} | {epoch_str} | {s.notes} |"
        )

    # Delta section: best vs second-best
    if len(sorted_runs) >= 2:
        best = sorted_runs[0]
        second = sorted_runs[1]
        lines += ["", "### Best vs Runner-Up", ""]
        if best.best_val_loss and second.best_val_loss:
            delta = second.best_val_loss - best.best_val_loss
            lines.append(f"- Val loss delta: {delta:+.4f} (best `{best.name}` vs `{second.name}`)")
        if best.best_metric_value and second.best_metric_value:
            delta = best.best_metric_value - second.best_metric_value
            lines.append(f"- {target_metric} delta: {delta:+.4f}")

    lines += [
        "",
        "### All Tracked Metrics (Best Values)",
        "",
    ]
    # Collect all metric names across runs
    all_metric_keys: list[str] = []
    for s in sorted_runs:
        for k in s.all_metrics:
            if k not in all_metric_keys and k not in ("epoch", "step"):
                all_metric_keys.append(k)

    if all_metric_keys:
        header = "| Run | " + " | ".join(all_metric_keys) + " |"
        sep = "| :--- | " + " | ".join("---:" for _ in all_metric_keys) + " |"
        lines += [header, sep]
        for s in sorted_runs:
            row_vals = [
                f"{s.all_metrics[k]:.4f}" if k in s.all_metrics else "—"
                for k in all_metric_keys
            ]
            lines.append(f"| `{s.name}` | " + " | ".join(row_vals) + " |")

    return "\n".join(lines) + "\n"


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize experiment history for BMAD revision phase."
    )
    parser.add_argument("logs_dir", type=Path,
                        help="Root directory to scan for metrics files")
    parser.add_argument("--metric", type=str, default="val/loss",
                        help="Target metric to rank by (default: val/loss)")
    parser.add_argument("--mode", choices=["min", "max"], default="min",
                        help="min for loss metrics, max for accuracy/F1 (default: min)")
    parser.add_argument("--top", type=int, default=None,
                        help="Show only top N runs")
    parser.add_argument("--output", type=Path, default=None,
                        help="Write markdown to this file (default: print to stdout)")
    args = parser.parse_args()

    if not args.logs_dir.exists():
        print(f"Error: Directory not found: {args.logs_dir}", file=sys.stderr)
        return 2

    run_files = discover_runs(args.logs_dir)
    if not run_files:
        print(f"No experiment metric files found in: {args.logs_dir}", file=sys.stderr)
        print("Expected: */version_*/metrics.csv, */metrics.csv, or *_metrics.csv/json",
              file=sys.stderr)
        return 1

    summaries: list[RunSummary] = []
    for path in run_files:
        s = extract_run_summary(path, args.logs_dir, args.metric, args.mode)
        if s:
            summaries.append(s)

    if not summaries:
        print("No valid runs could be parsed.", file=sys.stderr)
        return 1

    report = generate_summary_table(summaries, args.metric, args.mode, args.top)

    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"✓ Summary written to: {args.output}")
        print(f"  {len(summaries)} run(s) analyzed")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
