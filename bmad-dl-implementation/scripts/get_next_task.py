#!/usr/bin/env python3
"""
get_next_task.py — BMAD DL Lifecycle
Resolves the next Pending task from the design doc, respecting dependency order.
Cross-references the integration log to identify already-completed tasks.

Usage:
    python3 scripts/get_next_task.py <design_path> <integration_log_path> [--task-id TSK-00X]
    python3 scripts/get_next_task.py docs/design/03_Detailed_Design.md docs/implementation/04_Integration_Log.md
    python3 scripts/get_next_task.py docs/design/03_Detailed_Design.md docs/implementation/04_Integration_Log.md --task-id TSK-003

Exit codes:
    0 — task found and printed
    1 — no pending tasks / dependency not met
    2 — file error or argument error
"""

from __future__ import annotations

import argparse
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


# ── Parsing ────────────────────────────────────────────────────────────────────

TASK_ID_PATTERN = re.compile(r"TSK-\d+")
PLACEHOLDER = re.compile(r"^None$|^-$|^$", re.IGNORECASE)

COL_TASK_ID, COL_AGENT, COL_DESC, COL_REQ, COL_DEPS, COL_STATUS = 1, 2, 3, 4, 5, 6


def _clean(cell: str) -> str:
    return cell.strip().strip("`*[]")


def parse_tasks(design_text: str) -> list[Task]:
    tasks: list[Task] = []
    in_table = False
    for i, line in enumerate(design_text.splitlines(), 1):
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
        deps = TASK_ID_PATTERN.findall(deps_raw) if not PLACEHOLDER.match(deps_raw) else []
        tasks.append(Task(
            task_id=task_id,
            agent=_clean(cells[COL_AGENT]),
            description=_clean(cells[COL_DESC]),
            linked_req=_clean(cells[COL_REQ]),
            dependencies=deps,
            status=_clean(cells[COL_STATUS]) if len(cells) > COL_STATUS else "Pending",
            line_number=i,
        ))
    return tasks


def parse_completed_from_log(log_text: str) -> set[str]:
    """Extract Task IDs that appear in the integration log (= completed)."""
    return set(TASK_ID_PATTERN.findall(log_text))


# ── Resolution logic ───────────────────────────────────────────────────────────

def resolve_next_task(tasks: list[Task], completed: set[str],
                      requested_id: str | None = None) -> tuple[Task | None, str]:
    """
    Returns (task, reason) where reason explains why no task was returned if task is None.
    """
    task_map = {t.task_id: t for t in tasks}

    if requested_id:
        task = task_map.get(requested_id)
        if not task:
            return None, f"Task '{requested_id}' not found in design document."
        if task.task_id in completed:
            return None, f"Task '{requested_id}' is already completed (found in integration log)."
        unmet = [dep for dep in task.dependencies if dep not in completed]
        if unmet:
            return None, (
                f"Task '{requested_id}' has unmet dependencies: {', '.join(sorted(unmet))}. "
                f"Complete those tasks first."
            )
        return task, "ok"

    # Auto-resolve: find first pending task with all deps met
    for task in tasks:
        if task.task_id in completed:
            continue
        if task.status.lower() in ("done", "merged", "complete", "completed"):
            continue
        unmet = [dep for dep in task.dependencies if dep not in completed]
        if not unmet:
            return task, "ok"

    # Check if all tasks are done
    pending = [t for t in tasks if t.task_id not in completed and
               t.status.lower() not in ("done", "merged", "complete", "completed")]
    if not pending:
        return None, "All tasks are complete. The implementation phase is finished."

    # Pending tasks exist but all have unmet deps (shouldn't happen in a valid design)
    return None, (
        "All remaining tasks have unmet dependencies. "
        "This may indicate a circular dependency or missing completed task entries in the log."
    )


# ── Output ─────────────────────────────────────────────────────────────────────

def print_task(task: Task, completed: set[str], all_tasks: list[Task]) -> None:
    task_map = {t.task_id: t for t in all_tasks}
    total = len(all_tasks)
    done = len(completed)

    print(f"\n{'─' * 60}")
    print(f"  NEXT TASK: {task.task_id}  ({done}/{total} complete)")
    print(f"{'─' * 60}")
    print(f"  Agent:       {task.agent}")
    print(f"  Description: {task.description}")
    print(f"  Requirement: {task.linked_req}")

    if task.dependencies:
        dep_status = []
        for dep in task.dependencies:
            status = "✓ done" if dep in completed else "○ pending"
            dep_status.append(f"{dep} ({status})")
        print(f"  Depends on:  {', '.join(dep_status)}")
    else:
        print(f"  Depends on:  None (can start immediately)")

    remaining = [t.task_id for t in all_tasks
                 if t.task_id not in completed and t.task_id != task.task_id]
    if remaining:
        print(f"  Remaining:   {', '.join(remaining)}")
    print()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve next task from design doc.")
    parser.add_argument("design_path", type=Path)
    parser.add_argument("integration_log_path", type=Path)
    parser.add_argument("--task-id", type=str, default=None,
                        help="Specific task ID to validate and retrieve")
    args = parser.parse_args()

    if not args.design_path.exists():
        print(f"Error: Design file not found: {args.design_path}", file=sys.stderr)
        return 2

    design_text = args.design_path.read_text(encoding="utf-8")
    log_text = args.integration_log_path.read_text(encoding="utf-8") \
        if args.integration_log_path.exists() else ""

    tasks = parse_tasks(design_text)
    if not tasks:
        print("Error: No tasks found in design document.", file=sys.stderr)
        return 2

    completed = parse_completed_from_log(log_text)
    task, reason = resolve_next_task(tasks, completed, args.task_id)

    if task:
        print_task(task, completed, tasks)
        return 0
    else:
        print(f"\n  {reason}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
