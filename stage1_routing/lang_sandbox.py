"""Multi-language exercise loading + isolated test execution for Aider polyglot.

Reads each exercise's .meta/config.json to learn which files are the editable
'solution' files (the model writes these) and which are tests (hidden, kept for
running). Each run happens in a throwaway copy of the exercise dir.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

# Per-language test invocation. Pass == exit code 0.
LANG = {
    "python": {"cmd": ["python", "-m", "pytest", "-q"], "timeout": 120},
    "go":     {"cmd": ["go", "test", "./..."],          "timeout": 180},
    "rust":   {"cmd": ["cargo", "test", "--quiet"],     "timeout": 360},
}


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


@dataclass
class Exercise:
    name: str
    lang: str
    path: Path
    instruction: str
    solution_files: Dict[str, str] = field(default_factory=dict)  # relpath -> stub contents


def load_exercise(lang: str, ex_path: Path) -> Exercise:
    cfg = json.loads(_read(ex_path / ".meta" / "config.json"))
    sol = cfg.get("files", {}).get("solution", [])
    instr = _read(ex_path / ".docs" / "instructions.md")
    appendix = ex_path / ".docs" / "instructions.append.md"
    if appendix.exists():
        instr += "\n\n" + _read(appendix)
    sol_files = {rel: (_read(ex_path / rel) if (ex_path / rel).exists() else "")
                 for rel in sol}
    return Exercise(name=ex_path.name, lang=lang, path=ex_path,
                    instruction=instr, solution_files=sol_files)


@dataclass
class RunResult:
    passed: bool
    stdout: str
    rejected_edits: List[str] = field(default_factory=list)


def run_tests(ex: Exercise, files: Dict[str, str]) -> RunResult:
    spec = LANG[ex.lang]
    allowed = set(ex.solution_files.keys())
    rejected: List[str] = []
    with tempfile.TemporaryDirectory(prefix=f"ar_{ex.lang}_{ex.name}_") as tmp:
        tmp_path = Path(tmp)
        shutil.copytree(ex.path, tmp_path, dirs_exist_ok=True)
        for rel, content in (files or {}).items():
            if rel not in allowed:
                rejected.append(rel)        # only configured solution files may change
                continue
            target = tmp_path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        try:
            proc = subprocess.run(spec["cmd"], cwd=tmp_path, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=spec["timeout"])
            out = (proc.stdout or "") + (proc.stderr or "")
            return RunResult(proc.returncode == 0, out[-4000:], rejected)
        except subprocess.TimeoutExpired:
            return RunResult(False, f"TIMEOUT after {spec['timeout']}s", rejected)
        except FileNotFoundError as e:
            return RunResult(False, f"TOOLCHAIN MISSING: {e}", rejected)


def example_solution(ex: Exercise) -> Dict[str, str]:
    """Map the .meta/example.* reference onto the solution file path(s), for
    validating that the toolchain + task are sound before spending on models."""
    cfg = json.loads(_read(ex.path / ".meta" / "config.json"))
    examples = cfg.get("files", {}).get("example", [])
    sol = list(ex.solution_files.keys())
    out: Dict[str, str] = {}
    # primary code example maps to the primary solution file
    code_ex = [e for e in examples if not e.endswith(".toml")]
    if code_ex and sol:
        primary_sol = next((s for s in sol if not s.endswith(".toml")), sol[0])
        out[primary_sol] = _read(ex.path / code_ex[0])
    return out
