"""Run all tasks x arms x trials under budget; stream results to results.jsonl."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

import arms
from openrouter_client import OpenRouterClient
from sandbox import load_task

ROOT = Path(__file__).parent


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def main():
    _load_dotenv()
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    tasks_dir = ROOT / "tasks"
    task_dirs = sorted(d for d in tasks_dir.iterdir()
                       if d.is_dir() and (d / "meta.yaml").exists())
    if not task_dirs:
        print("No tasks found in tasks/. See tasks/README.md.")
        sys.exit(1)

    trials = int(cfg["trials"])
    arm_names = cfg["arms"]
    run_budget = float(cfg["budget"]["per_run_usd"])
    task_budget = float(cfg["budget"]["per_task_usd"])

    client = OpenRouterClient()
    results_path = ROOT / "results.jsonl"
    run_cost = 0.0

    with results_path.open("w") as f:
        for td in task_dirs:
            task = load_task(td)
            for arm_name in arm_names:
                arm_fn = arms.ARMS[arm_name]
                for trial in range(trials):
                    if run_cost >= run_budget:
                        print(f"\n[BUDGET] per-run ${run_budget} reached (${run_cost:.4f}). Stopping early.")
                        client.close()
                        _finish(run_cost, results_path)
                        return
                    traj = arm_fn(client, cfg, task, trial)
                    run_cost += traj.cost_usd
                    rec = {
                        "arm": traj.arm, "task": traj.task, "trial": traj.trial,
                        "difficulty": task.difficulty,
                        "solved": traj.solved, "attempts_used": traj.attempts_used,
                        "cost_usd": round(traj.cost_usd, 6),
                        "input_tokens": traj.input_tokens, "output_tokens": traj.output_tokens,
                        "cached_tokens": traj.cached_tokens, "latency_s": round(traj.latency_s, 2),
                        "error": traj.error,
                    }
                    f.write(json.dumps(rec) + "\n")
                    f.flush()
                    status = "PASS" if traj.solved else "fail"
                    flag = ""
                    if traj.error:
                        flag = f"  ERR:{traj.error[:60]}"
                    elif traj.cost_usd > task_budget:
                        flag = f"  [over per-task ${task_budget}]"
                    print(f"{arm_name:>2} | {task.name:<18} t{trial} | {status:<4} | "
                          f"{traj.attempts_used} att | ${traj.cost_usd:.4f}{flag}")

    client.close()
    _finish(run_cost, results_path)


def _finish(run_cost: float, results_path: Path):
    print(f"\nDone. Total spend ${run_cost:.4f}. Results -> {results_path}")
    print("Now run:  python report.py")


if __name__ == "__main__":
    main()
