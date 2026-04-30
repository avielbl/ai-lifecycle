#!/usr/bin/env python3
"""
baseline_classifier.py — BMAD DL Lifecycle
(Inspired by K-Dense claude-scientific-skills/scikit-learn/classification_pipeline.py)

Establishes sklearn baseline models before deep learning training.
Runs during TSK-001 (EDA) to set performance floors for REQ-PERF-* requirements.

Supports CSV tabular datasets. Outputs a markdown report with:
  - Multi-model cross-validation comparison (LR, RF, GradientBoosting)
  - Best model hyperparameter tuning
  - Feature importance ranking
  - Confusion matrix and classification report
  - Pass/fail verdict against PRD REQ-PERF targets

Reads PRD performance requirements if provided, same as parse_training_logs.py.

Usage:
    python3 scripts/baseline_classifier.py <data_csv> [prd_path] [--label-col LABEL] [--output report.md]
    python3 scripts/baseline_classifier.py data/features.csv docs/prd/01_PRD.md --label-col defective

Exit codes:
    0 — success
    1 — no suitable models found or all requirements failed
    2 — file/format error
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

warnings.filterwarnings("ignore")

# ── Optional deps ──────────────────────────────────────────────────────────────

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report, roc_auc_score,
    )
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class ModelResult:
    name: str
    cv_mean: float
    cv_std: float
    test_accuracy: float
    test_f1: float
    test_precision: float
    test_recall: float
    roc_auc: float | None = None
    best_params: dict = field(default_factory=dict)
    feature_importances: list[tuple[str, float]] = field(default_factory=list)
    confusion: list[list[int]] = field(default_factory=list)
    classification_report_str: str = ""


@dataclass
class PerfRequirement:
    req_id: str
    description: str
    acceptance_criteria: str
    metric_keyword: str | None


# ── PRD parsing (same logic as parse_training_logs.py) ────────────────────────

OPERATOR_PATTERN = re.compile(r"(>=|<=|>|<|=)\s*([\d.]+)")
PERF_REQ_PATTERN = re.compile(r"REQ-PERF-\d+")

METRIC_MAP = [
    (["f1", "f1-score", "f1 score"], "f1"),
    (["accuracy", "acc"], "accuracy"),
    (["precision"], "precision"),
    (["recall", "sensitivity"], "recall"),
    (["auc", "roc"], "roc_auc"),
]


def _guess_metric(text: str) -> str | None:
    text_lower = text.lower()
    for keywords, mapped in METRIC_MAP:
        if any(kw in text_lower for kw in keywords):
            return mapped
    return None


def _evaluate(criteria: str, achieved: float) -> str:
    match = OPERATOR_PATTERN.search(criteria)
    if not match:
        return "UNKNOWN"
    op, threshold = match.group(1), float(match.group(2))
    checks = {
        ">=": achieved >= threshold, "<=": achieved <= threshold,
        ">": achieved > threshold, "<": achieved < threshold,
        "=": abs(achieved - threshold) < 1e-6,
    }
    return "PASS" if checks.get(op, False) else "FAIL"


def parse_perf_requirements(prd_path: Path) -> list[PerfRequirement]:
    if not prd_path or not prd_path.exists():
        return []
    text = prd_path.read_text(encoding="utf-8")
    reqs: list[PerfRequirement] = []
    in_table = False
    for line in text.splitlines():
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
        reqs.append(PerfRequirement(
            req_id=req_id,
            description=cells[3],
            acceptance_criteria=cells[4],
            metric_keyword=_guess_metric(cells[3] + " " + cells[4]),
        ))
    return reqs


# ── CSV loading ────────────────────────────────────────────────────────────────

def load_csv(path: Path, label_col: str | None) -> tuple[list[str], list[list], list]:
    """Return (feature_names, X_rows, y_list)."""
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError("CSV is empty")

    columns = list(rows[0].keys())

    # Find label column
    if label_col and label_col in columns:
        target = label_col
    else:
        target = next(
            (c for c in columns if c.lower() in ("label", "class", "target", "y", "category")),
            None,
        )
    if target is None:
        raise ValueError(
            "No label column found. Specify with --label-col or use standard names: "
            "label, class, target, y, category"
        )

    feature_names = [c for c in columns if c != target]
    X_raw = [[row.get(c, "") for c in feature_names] for row in rows]
    y_raw = [row[target].strip() for row in rows]

    return feature_names, X_raw, y_raw


def _to_numeric_matrix(X_raw: list[list], feature_names: list[str]):
    """Return (X_numeric, numeric_feature_names) keeping only float-parseable columns."""
    if not HAS_NUMPY:
        raise RuntimeError("numpy required for baseline_classifier")
    numeric_cols: list[int] = []
    for col_idx in range(len(feature_names)):
        vals = []
        for row in X_raw:
            v = row[col_idx].strip()
            try:
                vals.append(float(v))
            except ValueError:
                break
        else:
            numeric_cols.append(col_idx)

    if not numeric_cols:
        raise ValueError("No numeric feature columns found in CSV")

    X = np.array([
        [float(row[ci]) if row[ci].strip() else float("nan") for ci in numeric_cols]
        for row in X_raw
    ], dtype=float)
    names = [feature_names[i] for i in numeric_cols]
    return X, names


# ── Model training ─────────────────────────────────────────────────────────────

def _get_models() -> dict:
    return {
        "Logistic Regression": (
            LogisticRegression(max_iter=1000, random_state=42),
            {"classifier__C": [0.1, 1.0, 10.0]},
        ),
        "Random Forest": (
            RandomForestClassifier(n_estimators=100, random_state=42),
            {"classifier__n_estimators": [100, 200], "classifier__max_depth": [10, None]},
        ),
        "Gradient Boosting": (
            GradientBoostingClassifier(n_estimators=100, random_state=42),
            {"classifier__n_estimators": [100, 200], "classifier__learning_rate": [0.05, 0.1]},
        ),
    }


def build_pipeline(estimator) -> "Pipeline":
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", estimator),
    ])


def run_baseline(
    X, y_encoded, feature_names: list[str], class_names: list[str], test_size: float = 0.2
) -> list[ModelResult]:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=test_size, stratify=y_encoded, random_state=42
    )

    results: list[ModelResult] = []
    cv_scores: dict[str, float] = {}
    models = _get_models()

    for name, (estimator, param_grid) in models.items():
        pipe = build_pipeline(estimator)
        scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1_weighted")
        cv_scores[name] = scores.mean()

    best_name = max(cv_scores, key=cv_scores.get)

    for name, (estimator, param_grid) in models.items():
        pipe = build_pipeline(estimator)
        scores = cross_val_score(pipe, X_train, y_train, cv=5, scoring="f1_weighted")

        # Tune best model; fit others without tuning
        if name == best_name:
            gs = GridSearchCV(pipe, param_grid, cv=5, scoring="f1_weighted", n_jobs=-1)
            gs.fit(X_train, y_train)
            fitted = gs.best_estimator_
            best_params = gs.best_params_
        else:
            pipe.fit(X_train, y_train)
            fitted = pipe
            best_params = {}

        y_pred = fitted.predict(X_test)
        is_binary = len(class_names) == 2

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
        prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
        rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)

        roc = None
        if is_binary and hasattr(fitted, "predict_proba"):
            try:
                y_prob = fitted.predict_proba(X_test)[:, 1]
                roc = roc_auc_score(y_test, y_prob)
            except Exception:
                pass

        # Feature importance
        fi: list[tuple[str, float]] = []
        clf = fitted.named_steps["classifier"]
        if hasattr(clf, "feature_importances_"):
            fi = sorted(
                zip(feature_names, clf.feature_importances_),
                key=lambda x: -x[1],
            )[:10]
        elif hasattr(clf, "coef_"):
            coefs = clf.coef_[0] if clf.coef_.ndim > 1 else clf.coef_
            fi = sorted(
                zip(feature_names, abs(coefs)),
                key=lambda x: -x[1],
            )[:10]

        cm = confusion_matrix(y_test, y_pred).tolist()
        cr = classification_report(y_test, y_pred, target_names=class_names, zero_division=0)

        results.append(ModelResult(
            name=name,
            cv_mean=scores.mean(),
            cv_std=scores.std(),
            test_accuracy=acc,
            test_f1=f1,
            test_precision=prec,
            test_recall=rec,
            roc_auc=roc,
            best_params=best_params,
            feature_importances=fi,
            confusion=cm,
            classification_report_str=cr,
        ))

    return sorted(results, key=lambda r: -r.test_f1)


# ── Report ─────────────────────────────────────────────────────────────────────

def generate_report(
    results: list[ModelResult],
    feature_names: list[str],
    class_names: list[str],
    data_path: Path,
    reqs: list[PerfRequirement],
    n_samples: int,
) -> str:
    lines: list[str] = []

    lines += [
        "# Baseline Classifier Report",
        f"*Dataset: `{data_path.name}` | {n_samples} samples | {len(class_names)} classes | {len(feature_names)} features*",
        "",
        "---",
        "",
        "## A. Model Comparison (5-Fold CV on F1-weighted)",
        "",
        "| Model | CV F1 (mean±std) | Test Acc | Test F1 | Test Prec | Test Recall | ROC AUC |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    best = results[0]
    for r in results:
        marker = " 🏆" if r is best else ""
        roc_str = f"{r.roc_auc:.4f}" if r.roc_auc is not None else "—"
        lines.append(
            f"| {r.name}{marker} | {r.cv_mean:.4f} ± {r.cv_std:.4f} | "
            f"{r.test_accuracy:.4f} | {r.test_f1:.4f} | {r.test_precision:.4f} | "
            f"{r.test_recall:.4f} | {roc_str} |"
        )

    lines += [
        "",
        f"**Best model: {best.name}**",
        "",
    ]
    if best.best_params:
        lines.append(f"Tuned hyperparameters: `{best.best_params}`")
        lines.append("")

    # Feature importance
    if best.feature_importances:
        lines += [
            "---",
            "",
            "## B. Top Feature Importances (Best Model)",
            "",
            "| Rank | Feature | Importance |",
            "| ---: | :--- | ---: |",
        ]
        for rank, (feat, imp) in enumerate(best.feature_importances, 1):
            bar = "█" * max(1, int(imp * 40))
            lines.append(f"| {rank} | {feat} | {imp:.4f} {bar} |")
        lines.append("")

    # Confusion matrix
    lines += [
        "---",
        "",
        "## C. Confusion Matrix (Best Model)",
        "",
        f"Classes: {', '.join(class_names)}",
        "",
        "```",
        "Predicted →",
    ]
    header_row = "Actual ↓    " + "  ".join(f"{c[:8]:>8}" for c in class_names)
    lines.append(header_row)
    for i, row in enumerate(best.confusion):
        row_str = f"{class_names[i][:8]:>8}  " + "  ".join(f"{v:>8}" for v in row)
        lines.append(row_str)
    lines += ["```", ""]

    # Classification report
    lines += [
        "## D. Classification Report (Best Model)",
        "",
        "```",
        best.classification_report_str,
        "```",
        "",
    ]

    # PRD requirement comparison
    if reqs:
        lines += [
            "---",
            "",
            "## E. PRD Requirement Status (Baseline)",
            "",
            "| Req ID | Description | Target | Achieved | Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
        metric_map = {
            "f1": best.test_f1,
            "accuracy": best.test_accuracy,
            "precision": best.test_precision,
            "recall": best.test_recall,
            "roc_auc": best.roc_auc,
        }
        for req in reqs:
            val = metric_map.get(req.metric_keyword or "")
            if val is not None:
                status = _evaluate(req.acceptance_criteria, val)
                val_str = f"{val:.4f}"
            else:
                status = "UNKNOWN"
                val_str = "N/A"
            icon = {"PASS": "✓", "FAIL": "✗", "UNKNOWN": "?"}.get(status, "?")
            lines.append(
                f"| {req.req_id} | {req.description[:35]} | `{req.acceptance_criteria}` | {val_str} | {icon} {status} |"
            )

        fails = sum(1 for r in reqs if metric_map.get(r.metric_keyword or "") is not None
                    and _evaluate(r.acceptance_criteria, metric_map[r.metric_keyword]) == "FAIL")
        lines += [
            "",
            f"> **Note:** This is a *baseline* result from classical ML. Deep learning is expected to improve on these scores.",
            f"> {'⚠ ' + str(fails) + ' requirement(s) not met even by baseline — review PRD targets.' if fails else '✓ Baseline meets all tracked requirements.'}",
        ]

    lines += [
        "",
        "---",
        "",
        "*Generated by `baseline_classifier.py` — BMAD DL Lifecycle (TSK-001)*",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Sklearn baseline classifier for BMAD DL")
    parser.add_argument("data_csv", type=Path)
    parser.add_argument("prd_path", type=Path, nargs="?", default=None)
    parser.add_argument("--label-col", type=str, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    if not HAS_SKLEARN:
        print("Error: scikit-learn not installed. Run: pip install scikit-learn", file=sys.stderr)
        return 2
    if not HAS_NUMPY:
        print("Error: numpy not installed. Run: pip install numpy", file=sys.stderr)
        return 2
    if not args.data_csv.exists():
        print(f"Error: File not found: {args.data_csv}", file=sys.stderr)
        return 2

    try:
        feature_names, X_raw, y_raw = load_csv(args.data_csv, args.label_col)
    except Exception as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        return 2

    try:
        X, numeric_feature_names = _to_numeric_matrix(X_raw, feature_names)
    except Exception as e:
        print(f"Error converting features: {e}", file=sys.stderr)
        return 2

    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_names = list(le.classes_)

    print(f"Dataset: {len(y)} samples, {len(numeric_feature_names)} features, {len(class_names)} classes")
    print(f"Classes: {class_names}")
    print("Running cross-validation and tuning best model...")

    try:
        results = run_baseline(X, y, numeric_feature_names, class_names, args.test_size)
    except Exception as e:
        print(f"Error during training: {e}", file=sys.stderr)
        return 2

    reqs = parse_perf_requirements(args.prd_path) if args.prd_path else []
    report = generate_report(results, numeric_feature_names, class_names,
                             args.data_csv, reqs, len(y))

    output = args.output or args.data_csv.parent / f"{args.data_csv.stem}_baseline_report.md"
    output.write_text(report, encoding="utf-8")
    print(f"\n✓ Report written to: {output}")
    print(f"  Best model: {results[0].name} | F1: {results[0].test_f1:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
