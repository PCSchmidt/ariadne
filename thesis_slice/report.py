"""Aggregate results.jsonl into decision tables + GREENLIGHT/CONDITIONAL/KILL.

Prints an overall table, a per-difficulty breakdown, and renders the thesis
verdict (B vs A1) on BOTH the full set and the 'hard' subset — the hard subset
is what actually exercises the evaluator/reflexion loop.
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
INF = float("inf")


def summarize(records):
    by_arm = defaultdict(list)
    for r in records:
        by_arm[r["arm"]].append(r)
    out = {}
    for arm, rs in by_arm.items():
        n = len(rs)
        solved = sum(1 for r in rs if r["solved"])
        total_cost = sum(r["cost_usd"] for r in rs)
        out[arm] = {
            "n": n,
            "solved": solved,
            "pass": solved / n if n else 0.0,
            "cost": total_cost,
            "cps": total_cost / solved if solved else INF,
            "mean_att": statistics.mean(r["attempts_used"] for r in rs) if rs else 0.0,
            "in_tok": sum(r["input_tokens"] for r in rs),
            "cached": sum(r["cached_tokens"] for r in rs),
        }
    return out


def print_table(summary, label):
    print(f"\n=== {label} ===")
    header = (f"{'arm':<4}{'pass':>8}{'solved':>8}{'runs':>6}"
              f"{'total$':>10}{'$/solved':>11}{'mean_att':>10}{'cached%':>9}")
    print(header)
    print("-" * len(header))
    for arm in sorted(summary):
        s = summary[arm]
        cps = f"{s['cps']:.4f}" if s["cps"] != INF else "n/a"
        cached_pct = 100.0 * s["cached"] / s["in_tok"] if s["in_tok"] else 0.0
        print(f"{arm:<4}{s['pass']*100:>7.1f}%{s['solved']:>8}{s['n']:>6}"
              f"{s['cost']:>10.4f}{cps:>11}{s['mean_att']:>10.2f}{cached_pct:>8.1f}%")


def verdict(summary, label):
    print(f"\n--- Verdict ({label}): thesis = B vs A1 ---")
    if "B" not in summary or "A1" not in summary:
        print("  need both A1 and B arms.")
        return
    b, a1 = summary["B"], summary["A1"]
    pass_ok = b["pass"] >= a1["pass"] - 1e-9
    cost_ok = b["cps"] <= a1["cps"] + 1e-9
    if pass_ok and cost_ok:
        v = "GREENLIGHT  - collective matches/beats single model at <= cost per solved."
    elif b["pass"] > a1["pass"] and not cost_ok:
        v = "CONDITIONAL - collective solves MORE but costs more per solved."
    elif not pass_ok and b["cps"] < a1["cps"]:
        v = "CONDITIONAL - collective cheaper per solved but lower pass rate."
    else:
        v = "KILL / RETHINK - collective not better on capability or cost."
    print(f"  {v}")
    a1_cps = f"{a1['cps']:.4f}" if a1["cps"] != INF else "n/a"
    b_cps = f"{b['cps']:.4f}" if b["cps"] != INF else "n/a"
    print(f"    A1: pass={a1['pass']*100:5.1f}%  $/solved={a1_cps}  mean_att={a1['mean_att']:.2f}")
    print(f"    B : pass={b['pass']*100:5.1f}%  $/solved={b_cps}  mean_att={b['mean_att']:.2f}")
    if max(a1["mean_att"], b["mean_att"]) < 1.01:
        print("    WARNING: mean_att ~1.0 -> evaluator loop never fired; this subset does")
        print("             NOT test the collective. Needs harder tasks.")


def main():
    path = ROOT / "results.jsonl"
    if not path.exists():
        print("No results.jsonl. Run `python runner.py` first.")
        return
    records = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if not records:
        print("results.jsonl is empty.")
        return

    n_tasks = len({r["task"] for r in records})
    print(f"\n########  Thesis Slice Report  —  {n_tasks} tasks, {len(records)} runs  ########")

    overall = summarize(records)
    print_table(overall, "OVERALL")
    if "A0" in overall and "A1" in overall:
        print(f"\nValue of retries (A1 - A0 pass): "
              f"{(overall['A1']['pass'] - overall['A0']['pass'])*100:+.1f} pts")
    verdict(overall, "overall")

    by_diff = defaultdict(list)
    for r in records:
        by_diff[r.get("difficulty", "unknown")].append(r)
    order = ["trivial", "easy", "medium", "hard", "unknown"]
    for diff in sorted(by_diff, key=lambda d: order.index(d) if d in order else 99):
        print_table(summarize(by_diff[diff]), f"difficulty: {diff}")

    if "hard" in by_diff:
        verdict(summarize(by_diff["hard"]), "HARD subset")

    print(f"\nNote: small N is signal, not proof. Inspect per-task rows in {path.name} too.")


if __name__ == "__main__":
    main()
