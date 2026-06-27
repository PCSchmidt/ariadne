"""Offline sanity check: exercises schema parsing + sandbox test execution with
NO network/API calls, so you can trust the plumbing before spending tokens."""
from __future__ import annotations

import sys
from pathlib import Path

from sandbox import load_task, run_attempt
from schemas import parse_worker

ROOT = Path(__file__).parent
ok = True


def check(name, cond):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    ok = ok and cond


print("schema parsing")
wo = parse_worker('```json\n{"files": {"solution.py": "x = 1"}, "notes": "hi"}\n```')
check("extracts JSON from fenced block", wo.files["solution.py"] == "x = 1")

print("sandbox: correct solution passes")
task = load_task(ROOT / "tasks" / "two_sum")
correct = (
    "def two_sum(nums, target):\n"
    "    seen = {}\n"
    "    for i, n in enumerate(nums):\n"
    "        if target - n in seen:\n"
    "            return [seen[target - n], i]\n"
    "        seen[n] = i\n"
)
res = run_attempt(task, {"solution.py": correct})
check("pytest passes on correct two_sum", res.passed)

print("sandbox: wrong solution fails")
res2 = run_attempt(task, {"solution.py": "def two_sum(nums, target):\n    return [0, 0]\n"})
check("pytest fails on wrong two_sum", not res2.passed)

print("sandbox: edits to test files are rejected")
res3 = run_attempt(task, {"test_solution.py": "def test_x():\n    assert True\n",
                          "solution.py": correct})
check("test-file edit rejected", "test_solution.py" in res3.rejected_edits)

print("\nSELFTEST:", "OK" if ok else "FAILURES")
sys.exit(0 if ok else 1)
