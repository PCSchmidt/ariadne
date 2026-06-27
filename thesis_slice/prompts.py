"""Prompt builders. Tests are HIDDEN from the generator on purpose: the model
sees the task + editable sources (+ prior failure output), never the test file,
so it can't hardcode expected values."""
from __future__ import annotations

from typing import Dict, List

from sandbox import Task

WORKER_SYSTEM = """You are an expert software engineer. Implement the task so the project's hidden test suite passes.

Rules:
- You may only edit these files: {allowed}
- You cannot see the tests. Implement the real behavior described; never hardcode or guess specific test values.
- Respond with ONLY a JSON object of this exact shape:
  {{"files": {{"<path>": "<full new file contents>"}}, "notes": "<one short line>"}}
- Include the COMPLETE contents of every file you change. No diffs, no placeholders, no commentary outside the JSON."""

EVALUATOR_SYSTEM = """You are a strict, independent code reviewer. A worker model attempted a task and the hidden test suite FAILED.
Given the task, the worker's submitted files, and the test output, diagnose the root cause and produce ONE concise constraint ("reflexion") to steer the next attempt. Do NOT rewrite the code yourself.

Respond with ONLY a JSON object: {"passed": false, "reflexion": "<1-2 sentences: the specific root cause and what the next attempt MUST do differently>"}"""


def _sources_block(sources: Dict[str, str]) -> str:
    parts = []
    for rel, content in sources.items():
        parts.append(f"## {rel}\n```\n{content}\n```")
    return "\n".join(parts)


def worker_user(task: Task, reflexions: List[str], last_stdout: str) -> str:
    parts = [f"# Task\n{task.instruction}", "# Editable files (current contents)", _sources_block(task.editable_sources)]
    if last_stdout:
        parts.append(f"# Previous attempt — failing test output\n```\n{last_stdout}\n```")
    if reflexions:
        parts.append("# Constraints learned from prior failures\n" + "\n".join(f"- {r}" for r in reflexions))
    return "\n\n".join(parts)


def evaluator_user(task: Task, submitted_files: Dict[str, str], stdout: str) -> str:
    parts = [f"# Task\n{task.instruction}", "# Worker submitted files", _sources_block(submitted_files),
             f"# Test output\n```\n{stdout}\n```"]
    return "\n\n".join(parts)
