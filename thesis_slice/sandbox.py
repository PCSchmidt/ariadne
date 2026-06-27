"""Task loading + isolated test execution.

Each attempt runs in a throwaway copy of the task directory so attempts never
contaminate each other. "Done" == pytest exits 0. Edits outside the task's
allow-list (notably test files) are rejected.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml


@dataclass
class Task:
    name: str
    path: Path
    instruction: str
    allowed_edit: List[str]
    difficulty: str
    editable_sources: Dict[str, str] = field(default_factory=dict)


def load_task(task_dir: Path) -> Task:
    meta = yaml.safe_load((task_dir / "meta.yaml").read_text()) or {}
    allowed = meta.get("allowed_edit", [])
    sources = {}
    for rel in allowed:
        p = task_dir / rel
        sources[rel] = p.read_text() if p.exists() else ""
    return Task(
        name=task_dir.name,
        path=task_dir,
        instruction=(task_dir / "task.md").read_text(),
        allowed_edit=allowed,
        difficulty=str(meta.get("difficulty", "unknown")),
        editable_sources=sources,
    )


@dataclass
class RunResult:
    passed: bool
    stdout: str
    rejected_edits: List[str] = field(default_factory=list)


def run_attempt(task: Task, files: Dict[str, str], pytest_timeout: int = 120) -> RunResult:
    rejected: List[str] = []
    with tempfile.TemporaryDirectory(prefix=f"ariadne_{task.name}_") as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(task.path, tmp_path, dirs_exist_ok=True)
        for rel, content in (files or {}).items():
            if rel not in task.allowed_edit:
                rejected.append(rel)           # never let the model edit tests
                continue
            target = tmp_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=tmp_path, capture_output=True, text=True, timeout=pytest_timeout,
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            return RunResult(passed=proc.returncode == 0, stdout=out[-4000:], rejected_edits=rejected)
        except subprocess.TimeoutExpired:
            return RunResult(passed=False, stdout="TIMEOUT running pytest", rejected_edits=rejected)
