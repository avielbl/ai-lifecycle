#!/usr/bin/env python3
"""
check_req_coverage.py — BMAD DL Lifecycle
Verifies every REQ-ID from the PRD is mapped to at least one component
in the architecture document's traceability table.

Usage:
    python3 scripts/check_req_coverage.py <prd_path> <architecture_path>
    python3 scripts/check_req_coverage.py docs/prd/01_PRD.md docs/architecture/02_Architecture.md

Exit codes:
    0 — full coverage
    1 — coverage gaps found
    2 — file error
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── Parsing ────────────────────────────────────────────────────────────────────

REQ_ID_PATTERN = re.compile(r"REQ-[A-Z]+-\d+")


def extract_req_ids(text: str) -> set[str]:
    """Extract all REQ-* identifiers from a markdown document."""
    return set(REQ_ID_PATTERN.findall(text))


def extract_req_ids_from_table(text: str, table_header_pattern: str) -> set[str]:
    """Extract REQ-IDs only from rows within a specific markdown table."""
    lines = text.splitlines()
    in_table = False
    ids: set[str] = []

    for line in lines:
        if re.search(table_header_pattern, line, re.IGNORECASE):
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue
        ids += REQ_ID_PATTERN.findall(line)

    return set(ids)


def extract_prd_req_ids(prd_text: str) -> set[str]:
    """Extract REQ-IDs defined in the PRD requirements table (section B)."""
    lines = prd_text.splitlines()
    in_table = False
    ids: set[str] = []
    col_req_id = 1

    for line in lines:
        if re.match(r"\|\s*Requirement\s*ID", line, re.IGNORECASE):
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r"^\s*\|[\s\-:|]+\|\s*$", line):
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue

        cells = line.split("|")
        if len(cells) < 3:
            continue

        cell = cells[col_req_id].strip().strip("`*[]")
        match = REQ_ID_PATTERN.match(cell)
        if match:
            ids.append(match.group())

    return set(ids)


# ── Result ─────────────────────────────────────────────────────────────────────

@dataclass
class CoverageResult:
    prd_req_ids: set[str] = field(default_factory=set)
    arch_req_ids: set[str] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)

    @property
    def uncovered(self) -> set[str]:
        """REQ-IDs in PRD not referenced anywhere in architecture."""
        return self.prd_req_ids - self.arch_req_ids

    @property
    def phantom(self) -> set[str]:
        """REQ-IDs in architecture that don't exist in PRD."""
        return self.arch_req_ids - self.prd_req_ids

    @property
    def passed(self) -> bool:
        return not self.errors and not self.uncovered


# ── Validation ─────────────────────────────────────────────────────────────────

def check_coverage(prd_path: Path, arch_path: Path) -> CoverageResult:
    result = CoverageResult()

    # Read files
    for path, label in [(prd_path, "PRD"), (arch_path, "Architecture")]:
        if not path.exists():
            result.errors.append(f"{label} file not found: {path}")

    if result.errors:
        return result

    prd_text = prd_path.read_text(encoding="utf-8")
    arch_text = arch_path.read_text(encoding="utf-8")

    # Extract IDs
    result.prd_req_ids = extract_prd_req_ids(prd_text)
    result.arch_req_ids = extract_req_ids(arch_text)

    if not result.prd_req_ids:
        result.errors.append(
            f"No REQ-IDs found in PRD ({prd_path}). "
            "Run validate_prd.py first to ensure the PRD is complete."
        )

    return result


# ── Report ─────────────────────────────────────────────────────────────────────

def print_report(result: CoverageResult) -> None:
    total = len(result.prd_req_ids)
    covered = total - len(result.uncovered)

    print(f"\nREQ Coverage: {covered}/{total} requirements mapped in architecture")
    print("─" * 60)

    if result.errors:
        for e in result.errors:
            print(f"✗ ERROR: {e}")
        return

    if not result.uncovered and not result.phantom:
        print("✓ PASSED — all PRD requirements are covered in the architecture.")
        return

    if result.uncovered:
        print(f"\n✗ FAILED — {len(result.uncovered)} requirement(s) not mapped to any architecture component:\n")
        for req_id in sorted(result.uncovered):
            print(f"  • {req_id} — not referenced in 02_Architecture.md")
        print(
            "\n  Fix: Add each missing REQ-ID to the 'Satisfies Requirement' column "
            "of the Component Design table in the architecture document."
        )

    if result.phantom:
        print(f"\n⚠  {len(result.phantom)} REQ-ID(s) in architecture not found in PRD:\n")
        for req_id in sorted(result.phantom):
            print(f"  • {req_id}")
        print("\n  These may be typos or requirements that were removed from the PRD.")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    if len(sys.argv) < 3:
        print(
            "Usage: python3 check_req_coverage.py <prd_path> <architecture_path>",
            file=sys.stderr,
        )
        return 2

    prd_path = Path(sys.argv[1])
    arch_path = Path(sys.argv[2])

    result = check_coverage(prd_path, arch_path)
    print_report(result)

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
