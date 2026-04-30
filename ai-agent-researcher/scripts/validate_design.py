#!/usr/bin/env python3
"""
validate_design.py — BMAD DL Lifecycle
Validates docs/design/03_Detailed_Design.md before implementation begins.

Checks:
  - TSK-001 exists and is assigned to Data-Agent (mandatory EDA task)
  - All tasks have a Linked Requirement (no orphaned tasks)
  - All REQ-IDs referenced exist in the PRD
  - All dependency references point to real Task IDs
  - No empty required fields

Usage:
    python3 scripts/validate_design.py <design_path> [prd_path]
    python3 scripts/validate_design.py docs/design/03_Detailed_Design.md docs/prd/01_PRD.md

Exit codes:
    0 — PASS
    1 — validation errors
    2 — file error
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Task:
    task_id: str
    agent: str
    description: str
    linked_req: str
    dependencies: list[str]
    status: str
    line_number: int


@dataclass
class DesignResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


# ── Parsing ────────────────────────────────────────────────────────────────────

TASK_ID_PATTERN = re.compile(r"TSK-\d+")
REQ_ID_PATTERN = re.compile(r"REQ-[A-Z]+-\d+")
PLACEHOLDER_PATTERN = re.compile(r"^\[.+\]$|^-$|^\.{3}$|^None$|^TBD$|^N/A$", re.IGNORECASE)

# Column indices in task table
COL_TASK_ID = 1
COL_AGENT = 2
COL_DESCRIPTION = 3
COL_REQ = 4
COL_DEPS = 5
COL_STATUS = 6


def _clean(cell: str) -> str:
    return cell.strip().strip("`*[]")


def _is_empty(value: str) -> bool:
    return not value or bool(PLACEHOLDER_PATTERN.match(value))


def parse_tasks(text: str) -> list[Task]:
    lines = text.splitlines()
    tasks: list[Task] = []
    in_table = False

    for i, line in enumerate(lines, start=1):
        if re.search(r"\|\s*Task\s*ID", line, re.IGNORECASE):
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
        if len(cells) < 6:
            continue

        task_id = _clean(cells[COL_TASK_ID])
        if not TASK_ID_PATTERN.match(task_id):
            continue

        deps_raw = _clean(cells[COL_DEPS]) if len(cells) > COL_DEPS else ""
        deps = TASK_ID_PATTERN.findall(deps_raw) if deps_raw and not _is_empty(deps_raw) else []

        tasks.append(Task(
            task_id=task_id,
            agent=_clean(cells[COL_AGENT]),
            description=_clean(cells[COL_DESCRIPTION]),
            linked_req=_clean(cells[COL_REQ]),
            dependencies=deps,
            status=_clean(cells[COL_STATUS]) if len(cells) > COL_STATUS else "",
            line_number=i,
        ))

    return tasks


def extract_prd_req_ids(prd_path: Path) -> set[str]:
    if not prd_path or not prd_path.exists():
        return set()
    text = prd_path.read_text(encoding="utf-8")
    return set(REQ_ID_PATTERN.findall(text))


# ── Validation checks ──────────────────────────────────────────────────────────

def check_tsk_001_eda(tasks: list[Task], result: DesignResult) -> None:
    task_ids = {t.task_id for t in tasks}
    if "TSK-001" not in task_ids:
        result.errors.append(
            "TSK-001 is missing. The first task MUST always be assigned to "
            "Data-Agent for Exploratory Data Analysis (EDA)."
        )
        return

    tsk001 = next(t for t in tasks if t.task_id == "TSK-001")
    if "data" not in tsk001.agent.lower():
        result.errors.append(
            f"TSK-001 is assigned to '{tsk001.agent}' but MUST be assigned to "
            f"'Data-Agent'. TSK-001 is always the EDA task."
        )
    if not re.search(r"EDA|exploratory|analysis|quality", tsk001.description, re.IGNORECASE):
        result.warnings.append(
            "TSK-001 description does not mention EDA, exploratory analysis, or data quality. "
            "Ensure this task covers class distributions, missing values, annotation quality, "
            "and dataset split verification."
        )


def check_linked_requirements(tasks: list[Task], prd_req_ids: set[str],
                               result: DesignResult) -> None:
    for task in tasks:
        if _is_empty(task.linked_req):
            result.errors.append(
                f"Line {task.line_number}: {task.task_id} has no Linked Requirement. "
                f"Every task must trace back to a PRD requirement."
            )
            continue

        req_ids_in_cell = REQ_ID_PATTERN.findall(task.linked_req)
        if not req_ids_in_cell:
            result.errors.append(
                f"Line {task.line_number}: {task.task_id} linked requirement "
                f"'{task.linked_req}' does not match REQ-*-* format."
            )
            continue

        if prd_req_ids:
            for req_id in req_ids_in_cell:
                if req_id not in prd_req_ids:
                    result.errors.append(
                        f"Line {task.line_number}: {task.task_id} references "
                        f"'{req_id}' which does not exist in the PRD."
                    )


def check_dependency_references(tasks: list[Task], result: DesignResult) -> None:
    valid_ids = {t.task_id for t in tasks}
    for task in tasks:
        for dep in task.dependencies:
            if dep not in valid_ids:
                result.errors.append(
                    f"Line {task.line_number}: {task.task_id} depends on "
                    f"'{dep}' which is not defined in this design document."
                )


def check_no_empty_fields(tasks: list[Task], result: DesignResult) -> None:
    for task in tasks:
        if _is_empty(task.agent):
            result.errors.append(
                f"Line {task.line_number}: {task.task_id} has no assigned Agent."
            )
        if _is_empty(task.description):
            result.errors.append(
                f"Line {task.line_number}: {task.task_id} has an empty Description."
            )


def check_duplicate_task_ids(tasks: list[Task], result: DesignResult) -> None:
    seen: dict[str, int] = {}
    for task in tasks:
        if task.task_id in seen:
            result.errors.append(
                f"Duplicate Task ID '{task.task_id}' at line {task.line_number} "
                f"(first seen at line {seen[task.task_id]})."
            )
        else:
            seen[task.task_id] = task.line_number


def check_circular_dependencies(tasks: list[Task], result: DesignResult) -> None:
    graph: dict[str, list[str]] = {t.task_id: t.dependencies for t in tasks}

    def has_cycle(node: str, visited: set, stack: set) -> bool:
        visited.add(node)
        stack.add(node)
        for dep in graph.get(node, []):
            if dep not in visited:
                if has_cycle(dep, visited, stack):
                    return True
            elif dep in stack:
                return True
        stack.discard(node)
        return False

    visited: set[str] = set()
    for task_id in graph:
        if task_id not in visited:
            if has_cycle(task_id, visited, set()):
                result.errors.append(
                    f"Circular dependency detected involving task '{task_id}'."
                )


# ── Main validation ────────────────────────────────────────────────────────────

def validate(design_path: Path, prd_path: Path | None = None) -> DesignResult:
    result = DesignResult()

    if not design_path.exists():
        result.errors.append(f"Design file not found: {design_path}")
        return result

    text = design_path.read_text(encoding="utf-8")
    tasks = parse_tasks(text)
    result.tasks = tasks

    if not tasks:
        result.errors.append(
            "No tasks found in the design document. "
            "Ensure the table contains a 'Task ID' column header."
        )
        return result

    prd_req_ids = extract_prd_req_ids(prd_path) if prd_path else set()

    check_tsk_001_eda(tasks, result)
    check_duplicate_task_ids(tasks, result)
    check_linked_requirements(tasks, prd_req_ids, result)
    check_dependency_references(tasks, result)
    check_no_empty_fields(tasks, result)
    check_circular_dependencies(tasks, result)

    return result


def print_report(design_path: Path, result: DesignResult) -> None:
    print(f"\nValidating: {design_path}")
    print(f"Tasks found: {len(result.tasks)}")
    print("─" * 60)

    if result.passed and not result.warnings:
        print("✓ Design validation PASSED — ready for implementation.")
        return

    if result.errors:
        print(f"✗ FAILED — {len(result.errors)} error(s):\n")
        for i, err in enumerate(result.errors, 1):
            print(f"  {i}. {err}")

    if result.warnings:
        print(f"\n⚠  {len(result.warnings)} warning(s):\n")
        for w in result.warnings:
            print(f"  • {w}")

    if result.passed:
        print("\n✓ Design validation PASSED (with warnings).")


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: python3 validate_design.py <design_path> [prd_path]",
            file=sys.stderr,
        )
        return 2

    design_path = Path(sys.argv[1])
    prd_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    result = validate(design_path, prd_path)
    print_report(design_path, result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
