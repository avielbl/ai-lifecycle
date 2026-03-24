#!/usr/bin/env python3
"""
validate_prd.py — BMAD DL Lifecycle
Validates docs/prd/01_PRD.md for completeness before architecture begins.

Usage:
    python3 scripts/validate_prd.py <prd_path>
    python3 scripts/validate_prd.py docs/prd/01_PRD.md

Exit codes:
    0 — PASS
    1 — validation errors found
    2 — file not found or unreadable
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

REQUIRED_SECTIONS = ["Project Overview", "Traceable Requirements", "Status"]
REQUIRED_REQ_CATEGORIES = {"System", "Data", "Performance"}
REQUIRED_REQ_PREFIXES = {"REQ-SYS", "REQ-DATA", "REQ-PERF"}
STATUS_APPROVAL_PATTERN = re.compile(r"\[x\]\s*Approved", re.IGNORECASE)

# Table column indices (0-based after splitting on |)
COL_REQ_ID = 1
COL_CATEGORY = 2
COL_DESCRIPTION = 3
COL_ACCEPTANCE = 4


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Requirement:
    req_id: str
    category: str
    description: str
    acceptance_criteria: str
    line_number: int


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ── Parsing helpers ────────────────────────────────────────────────────────────

def _clean_cell(cell: str) -> str:
    return cell.strip().strip("*`[]")


def _is_separator_row(row: str) -> bool:
    return bool(re.match(r"^\s*\|[\s\-:|]+\|\s*$", row))


def parse_requirements_table(lines: list[str]) -> list[Requirement]:
    """Extract requirement rows from the markdown table in section B."""
    requirements: list[Requirement] = []
    in_table = False

    for i, line in enumerate(lines, start=1):
        if re.match(r"\|\s*Requirement\s*ID", line, re.IGNORECASE):
            in_table = True
            continue
        if not in_table:
            continue
        if _is_separator_row(line):
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue

        cells = line.split("|")
        if len(cells) < 5:
            continue

        req_id = _clean_cell(cells[COL_REQ_ID])
        category = _clean_cell(cells[COL_CATEGORY])
        description = _clean_cell(cells[COL_DESCRIPTION])
        acceptance = _clean_cell(cells[COL_ACCEPTANCE])

        # Skip placeholder / header rows
        if not req_id or req_id.startswith(":") or "Requirement" in req_id:
            continue

        requirements.append(Requirement(
            req_id=req_id,
            category=category,
            description=description,
            acceptance_criteria=acceptance,
            line_number=i,
        ))

    return requirements


def find_sections(text: str) -> set[str]:
    """Return set of section headings found (### A., ### B., etc.)."""
    return set(re.findall(r"###\s+[A-Z]\.\s+(.+)", text))


# ── Validation checks ──────────────────────────────────────────────────────────

def check_required_sections(text: str, result: ValidationResult) -> None:
    sections = find_sections(text)
    for required in REQUIRED_SECTIONS:
        if not any(required.lower() in s.lower() for s in sections):
            result.add_error(f"Missing required section: '### X. {required}'")


def check_requirements_table(lines: list[str], result: ValidationResult) -> list[Requirement]:
    reqs = parse_requirements_table(lines)

    if not reqs:
        result.add_error(
            "No requirements found in the Traceable Requirements table. "
            "Ensure the table header contains 'Requirement ID'."
        )
        return []

    return reqs


def check_req_id_format(reqs: list[Requirement], result: ValidationResult) -> None:
    pattern = re.compile(r"^REQ-[A-Z]+-\d+$")
    for req in reqs:
        if not pattern.match(req.req_id):
            result.add_error(
                f"Line {req.line_number}: Invalid REQ-ID format '{req.req_id}'. "
                f"Expected pattern: REQ-<CATEGORY>-<NUMBER> (e.g. REQ-PERF-01)"
            )


def check_category_coverage(reqs: list[Requirement], result: ValidationResult) -> None:
    found_prefixes = {req.req_id.rsplit("-", 1)[0] for req in reqs}
    missing = REQUIRED_REQ_PREFIXES - found_prefixes
    for prefix in sorted(missing):
        result.add_error(
            f"No requirement with prefix '{prefix}-' found. "
            f"Every PRD must include at least one {prefix} requirement."
        )


def check_empty_fields(reqs: list[Requirement], result: ValidationResult) -> None:
    placeholder_patterns = [
        re.compile(r"^\[.+\]$"),   # [Placeholder text]
        re.compile(r"^\.{3}$"),    # ...
        re.compile(r"^-$"),        # -
        re.compile(r"^TBD$", re.IGNORECASE),
    ]

    def _is_placeholder(value: str) -> bool:
        return not value or any(p.match(value) for p in placeholder_patterns)

    for req in reqs:
        if _is_placeholder(req.description):
            result.add_error(
                f"Line {req.line_number}: REQ '{req.req_id}' has an empty or placeholder Description."
            )
        if _is_placeholder(req.acceptance_criteria):
            result.add_error(
                f"Line {req.line_number}: REQ '{req.req_id}' has an empty or placeholder Acceptance Criteria. "
                f"Every requirement must have measurable acceptance criteria."
            )
        if _is_placeholder(req.category):
            result.add_error(
                f"Line {req.line_number}: REQ '{req.req_id}' has an empty Category."
            )


def check_status_approval(text: str, result: ValidationResult) -> None:
    if not STATUS_APPROVAL_PATTERN.search(text):
        result.add_error(
            "Status section does not show approval. "
            "Expected: '* [x] Approved for Architecture Design'"
        )


def check_duplicate_req_ids(reqs: list[Requirement], result: ValidationResult) -> None:
    seen: dict[str, int] = {}
    for req in reqs:
        if req.req_id in seen:
            result.add_error(
                f"Duplicate REQ-ID '{req.req_id}' found at line {req.line_number} "
                f"(first seen at line {seen[req.req_id]})."
            )
        else:
            seen[req.req_id] = req.line_number


def check_minimum_requirements(reqs: list[Requirement], result: ValidationResult) -> None:
    if len(reqs) < 3:
        result.add_warning(
            f"Only {len(reqs)} requirement(s) found. A meaningful PRD typically has "
            f"at least one each of REQ-SYS, REQ-DATA, and REQ-PERF."
        )


# ── Main ───────────────────────────────────────────────────────────────────────

def validate(prd_path: Path) -> ValidationResult:
    result = ValidationResult()

    try:
        text = prd_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        result.add_error(f"File not found: {prd_path}")
        return result
    except OSError as e:
        result.add_error(f"Cannot read file: {e}")
        return result

    lines = text.splitlines()

    check_required_sections(text, result)
    reqs = check_requirements_table(lines, result)

    if reqs:
        check_req_id_format(reqs, result)
        check_category_coverage(reqs, result)
        check_empty_fields(reqs, result)
        check_duplicate_req_ids(reqs, result)
        check_minimum_requirements(reqs, result)

    check_status_approval(text, result)

    return result


def print_report(prd_path: Path, result: ValidationResult) -> None:
    print(f"\nValidating: {prd_path}")
    print("─" * 60)

    if result.passed and not result.warnings:
        print("✓ PRD validation PASSED — ready for architecture phase.")
        return

    if result.errors:
        print(f"✗ FAILED — {len(result.errors)} error(s) must be fixed:\n")
        for i, err in enumerate(result.errors, 1):
            print(f"  {i}. {err}")

    if result.warnings:
        print(f"\n⚠  {len(result.warnings)} warning(s):\n")
        for w in result.warnings:
            print(f"  • {w}")

    if result.passed:
        print("\n✓ PRD validation PASSED (with warnings).")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 validate_prd.py <prd_path>", file=sys.stderr)
        print("Example: python3 validate_prd.py docs/prd/01_PRD.md", file=sys.stderr)
        return 2

    prd_path = Path(sys.argv[1])
    result = validate(prd_path)
    print_report(prd_path, result)

    if not result.passed:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
