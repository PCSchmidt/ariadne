"""Pre-flight: apply each task's reference example and confirm tests pass.
Proves the toolchains run and the selected tasks are sound BEFORE model spend.
Also times each language so we know the run budget."""
from __future__ import annotations

import time
from pathlib import Path

import yaml

from lang_sandbox import load_exercise, run_tests, example_solution
from task_select import select

ROOT = Path(__file__).parent


def main():
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    chosen = select(cfg["languages"], cfg["n_per_lang"], cfg["seed"])
    allok = True
    for lang, exs in chosen.items():
        print(f"\n=== {lang} ===")
        t_lang = time.time()
        for ex_path in exs:
            ex = load_exercise(lang, ex_path)
            ref = example_solution(ex)
            t0 = time.time()
            res = run_tests(ex, ref)
            dt = time.time() - t0
            ok = res.passed
            allok = allok and ok
            mark = "OK " if ok else "BAD"
            print(f"  [{mark}] {ex.name:<24} {dt:5.1f}s")
            if not ok:
                print("      " + res.stdout.strip().replace("\n", "\n      ")[-600:])
        print(f"  ({lang} total {time.time()-t_lang:.0f}s)")
    print("\nALL EXAMPLES PASS" if allok else "\nSOME EXAMPLES FAILED (fix selection/toolchain before running)")


if __name__ == "__main__":
    main()
