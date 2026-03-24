#!/usr/bin/env python3
"""
parse_training_logs.py — BMAD DL Lifecycle
Extracts key metrics from training logs and compares against PRD performance requirements.
Produces a compact structured summary for the analysis skill.

Supported log formats:
  - CSV  (columns: epoch, train_loss, val_loss, + any metric columns)
  - JSON (list of epoch dicts, or {"history": [...]} wrapper)

Usage:
    python3 scripts/parse_training_logs.py <log_path> [prd_path] [--format csv|json]
    python3 scripts/parse_training_logs.py docs/experiments/run_001_metrics.csv docs/prd/01_PRD.md

Exit codes:
    0 — success
    2 — file/format error
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class EpochMetrics:
    epoch: int
    train_loss: float | None
    val_loss: float | None
    extra: dict[str, float] = field(default_factory=dict)


@dataclass
class PerfRequirement:
    req_id: str
    description: str
    acceptance_criteria: str
    metric_keyword: str | None  # best-guess keyword match to log columns


@dataclass
class MetricComparison:
    req_id: str
    description: str
    target_raw: str
    metric_name: str | None
    achieved: float | None
    status: str  # PASS / FAIL / UNKNOWN


# ── PRD parsing ────────────────────────────────────────────────────────────────

OPERATOR_PATTERN = re.compile(r"(>=|<=|>|<|=)\s*([\d.]+)")
PERF_REQ_PATTERN = re.compile(r"REQ-PERF-\d+")


def parse_perf_requirements(prd_path: Path) -> list[PerfRequirement]:
    if not prd_path or not prd_path.exists():
        return []

    text = prd_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    reqs: list[PerfRequirement] = []
    in_table = False

    for line in lines:
        if re.search(r"\|\s*Requirement\s*ID", line, re.IGNORECASE):
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue

        cells = [c.strip().strip("`*[]") for c in line.split("|")]
        if len(cells) < 5:
            continue

        req_id = cells[1]
        if not PERF_REQ_PATTERN.match(req_id):
            continue

        description = cells[3]
        criteria = cells[4]

        # Guess metric keyword from description/criteria
        keyword = _guess_metric_keyword(description + " " + criteria)

        reqs.append(PerfRequirement(
            req_id=req_id,
            description=description,
            acceptance_criteria=criteria,
            metric_keyword=keyword,
        ))

    return reqs


def _guess_metric_keyword(text: str) -> str | None:
    """Map common metric phrases to likely column names."""
    text_lower = text.lower()
    candidates = [
        (["f1", "f1-score", "f1 score"], "f1"),
        (["accuracy", "acc"], "acc"),
        (["precision"], "precision"),
        (["recall", "sensitivity"], "recall"),
        (["auc", "roc"], "auc"),
        (["latency", "inference time", "ms per"], "latency"),
        (["loss", "val_loss"], "val_loss"),
        (["mae", "mean absolute error"], "mae"),
        (["mse", "mean squared error"], "mse"),
        (["r2", "r squared", "r^2"], "r2"),
    ]
    for keywords, mapped in candidates:
        if any(kw in text_lower for kw in keywords):
            return mapped
    return None


def _parse_target(criteria: str) -> tuple[str | None, float | None]:
    """Extract operator and threshold from acceptance criteria string."""
    match = OPERATOR_PATTERN.search(criteria)
    if match:
        return match.group(1), float(match.group(2))
    return None, None


def _evaluate_against_target(criteria: str, achieved: float) -> str:
    op, threshold = _parse_target(criteria)
    if op is None or threshold is None:
        return "UNKNOWN"
    checks = {
        ">=": achieved >= threshold,
        "<=": achieved <= threshold,
        ">": achieved > threshold,
        "<": achieved < threshold,
        "=": abs(achieved - threshold) < 1e-6,
    }
    return "PASS" if checks.get(op, False) else "FAIL"


# ── Log parsing ────────────────────────────────────────────────────────────────

def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_csv_log(path: Path) -> list[EpochMetrics]:
    epochs: list[EpochMetrics] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names
            row_lower = {k.lower().strip(): v for k, v in row.items()}
            epoch = int(_to_float(row_lower.get("epoch", len(epochs))) or len(epochs))
            train_loss = _to_float(row_lower.get("train_loss") or row_lower.get("loss"))
            val_loss = _to_float(row_lower.get("val_loss") or row_lower.get("val loss"))
            extra = {
                k: _to_float(v)
                for k, v in row_lower.items()
                if k not in ("epoch", "train_loss", "loss", "val_loss", "val loss")
                and _to_float(v) is not None
            }
            epochs.append(EpochMetrics(epoch=epoch, train_loss=train_loss,
                                        val_loss=val_loss, extra=extra))
    return epochs


def parse_json_log(path: Path) -> list[EpochMetrics]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        # {"history": [...]} or {"logs": [...]}
        for key in ("history", "logs", "epochs", "metrics"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
    if not isinstance(data, list):
        raise ValueError("JSON log must be a list of epoch dicts or {history: [...]}")

    epochs: list[EpochMetrics] = []
    for i, entry in enumerate(data):
        entry_lower = {k.lower(): v for k, v in entry.items()}
        epoch = int(_to_float(entry_lower.get("epoch", i)) or i)
        train_loss = _to_float(entry_lower.get("train_loss") or entry_lower.get("loss"))
        val_loss = _to_float(entry_lower.get("val_loss"))
        extra = {
            k: _to_float(v)
            for k, v in entry_lower.items()
            if k not in ("epoch", "train_loss", "loss", "val_loss")
            and _to_float(v) is not None
        }
        epochs.append(EpochMetrics(epoch=epoch, train_loss=train_loss,
                                    val_loss=val_loss, extra=extra))
    return epochs


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix in (".csv", ".tsv"):
        return "csv"
    # Sniff first line
    first_line = path.read_text(encoding="utf-8", errors="ignore")[:200]
    return "json" if first_line.strip().startswith(("[", "{")) else "csv"


# ── Analysis ───────────────────────────────────────────────────────────────────

def find_best_epoch(epochs: list[EpochMetrics]) -> EpochMetrics | None:
    """Return epoch with lowest val_loss (common proxy for best checkpoint)."""
    candidates = [e for e in epochs if e.val_loss is not None]
    return min(candidates, key=lambda e: e.val_loss) if candidates else (epochs[-1] if epochs else None)


def find_metric_value(epochs: list[EpochMetrics], keyword: str) -> float | None:
    """Find the best value for a metric keyword across all epochs."""
    # Try exact match first, then substring
    all_values: list[float] = []
    for ep in epochs:
        for col, val in ep.extra.items():
            if val is not None and (col == keyword or keyword in col):
                all_values.append(val)
        # Also check train/val loss
        if keyword in ("val_loss", "loss") and ep.val_loss is not None:
            all_values.append(ep.val_loss)

    if not all_values:
        return None
    # For loss metrics return minimum; for score metrics return maximum
    loss_keywords = ("loss", "mae", "mse", "error", "latency")
    if any(lk in keyword.lower() for lk in loss_keywords):
        return min(all_values)
    return max(all_values)


def compare_requirements(reqs: list[PerfRequirement],
                          epochs: list[EpochMetrics]) -> list[MetricComparison]:
    results: list[MetricComparison] = []
    for req in reqs:
        metric_name = req.metric_keyword
        achieved = find_metric_value(epochs, metric_name) if metric_name else None
        status = _evaluate_against_target(req.acceptance_criteria, achieved) \
            if achieved is not None else "UNKNOWN"
        results.append(MetricComparison(
            req_id=req.req_id,
            description=req.description,
            target_raw=req.acceptance_criteria,
            metric_name=metric_name,
            achieved=achieved,
            status=status,
        ))
    return results


# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(epochs: list[EpochMetrics], comparisons: list[MetricComparison],
                 log_path: Path) -> None:
    best = find_best_epoch(epochs)
    last = epochs[-1] if epochs else None

    print(f"\n{'═' * 60}")
    print(f"  TRAINING LOG ANALYSIS: {log_path.name}")
    print(f"{'═' * 60}")
    print(f"  Total epochs:  {len(epochs)}")

    if best:
        print(f"  Best epoch:    {best.epoch}  (val_loss = {best.val_loss:.4f})")
    if last and best and last.epoch != best.epoch:
        print(f"  Final epoch:   {last.epoch}  (val_loss = {last.val_loss:.4f})")

    # Overfit delta
    if best and best.train_loss is not None and best.val_loss is not None:
        delta = best.val_loss - best.train_loss
        overfit_note = "⚠ possible overfitting" if delta > 0.15 else "ok"
        print(f"  Overfit delta: {delta:+.4f}  ({overfit_note})")

    # All metrics at best epoch
    if best and best.extra:
        print(f"\n  Metrics at best epoch ({best.epoch}):")
        for k, v in sorted(best.extra.items()):
            if v is not None:
                print(f"    {k:<20} {v:.4f}")

    # PRD requirement comparison
    if comparisons:
        print(f"\n{'─' * 60}")
        print("  PRD REQUIREMENT STATUS")
        print(f"{'─' * 60}")
        col_w = max(len(c.req_id) for c in comparisons) + 2
        for c in comparisons:
            achieved_str = f"{c.achieved:.4f}" if c.achieved is not None else "N/A (no matching metric)"
            icon = {"PASS": "✓", "FAIL": "✗", "UNKNOWN": "?"}.get(c.status, "?")
            print(f"  {icon} {c.req_id:<{col_w}} | {c.description[:30]:<30} | "
                  f"Target: {c.target_raw:<15} | Achieved: {achieved_str:<10} | {c.status}")

        failures = [c for c in comparisons if c.status == "FAIL"]
        unknowns = [c for c in comparisons if c.status == "UNKNOWN"]
        if failures:
            print(f"\n  ✗ {len(failures)} requirement(s) not met — revision cycle recommended.")
        elif unknowns:
            print(f"\n  ? {len(unknowns)} requirement(s) could not be automatically evaluated.")
            print(f"    Check metric column names match PRD keywords.")
        else:
            print(f"\n  ✓ All tracked requirements met.")
    else:
        print("\n  (No PRD provided — skipping requirement comparison)")

    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Parse training logs for BMAD analysis skill.")
    parser.add_argument("log_path", type=Path)
    parser.add_argument("prd_path", type=Path, nargs="?", default=None)
    parser.add_argument("--format", choices=["csv", "json"], default=None)
    args = parser.parse_args()

    if not args.log_path.exists():
        print(f"Error: Log file not found: {args.log_path}", file=sys.stderr)
        return 2

    fmt = args.format or detect_format(args.log_path)
    try:
        epochs = parse_csv_log(args.log_path) if fmt == "csv" else parse_json_log(args.log_path)
    except Exception as e:
        print(f"Error parsing log file: {e}", file=sys.stderr)
        return 2

    if not epochs:
        print("Error: No epoch data found in log file.", file=sys.stderr)
        return 2

    reqs = parse_perf_requirements(args.prd_path) if args.prd_path else []
    comparisons = compare_requirements(reqs, epochs)
    print_report(epochs, comparisons, args.log_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
