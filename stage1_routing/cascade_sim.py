"""Stage 2 (offline): simulate test-gated cost cascades from the Stage 1 matrix.

A cascade is an ordered list of models. For each task we try them in order, pay
each one we call, and STOP at the first model whose output passes the tests.
Because the matrix already records each model's independent one-shot result and
cost per task, every cascade is reconstructable with ZERO new API spend:

    solved(cascade, task) = OR over members
    cost(cascade, task)   = sum of member costs until (and including) first solve;
                            if none solve, sum of all member costs

This captures the realistic, verifier-gated cost router (run cheap, run tests,
escalate on failure). It does NOT model tier-2 seeing tier-1's failure output
(correlated reflexion) -- that needs live runs and would only help pass rate.
"""
from __future__ import annotations

import itertools
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent


def load():
    recs = [json.loads(l) for l in (ROOT / "matrix_results.jsonl").read_text().splitlines() if l.strip()]
    agg = defaultdict(lambda: {"solved": False, "cost": 0.0, "n": 0})
    for r in recs:
        a = agg[(r["model"], r["lang"], r["task"])]
        a["solved"] = a["solved"] or r["solved"]
        a["cost"] += r["cost_usd"]; a["n"] += 1
    for a in agg.values():
        a["cost"] /= max(a["n"], 1)
    return agg


def main():
    ROUTERS = {"openrouter/auto"}
    agg = load()
    models = sorted({k[0] for k in agg if k[0] not in ROUTERS})  # base models only
    tasks = sorted({(k[1], k[2]) for k in agg})

    def solved(m, t): return agg.get((m,) + t, {"solved": False})["solved"]
    def cost(m, t): return agg.get((m,) + t, {"cost": 0.0})["cost"]

    def eval_cascade(order):
        total_cost = 0.0; n_solved = 0; depth_sum = 0
        for t in tasks:
            paid = 0.0; hit = False; depth = 0
            for m in order:
                paid += cost(m, t); depth += 1
                if solved(m, t):
                    hit = True; break
            total_cost += paid; depth_sum += depth
            if hit: n_solved += 1
        n = len(tasks)
        return {"pass": n_solved / n, "solved": n_solved, "cost": total_cost,
                "cps": total_cost / n_solved if n_solved else float("inf"),
                "mean_depth": depth_sum / n}

    # baselines
    single = {m: eval_cascade([m]) for m in models}
    best_model = max(models, key=lambda m: single[m]["pass"])
    base = single[best_model]
    union_pass = sum(any(solved(m, t) for m in models) for t in tasks) / len(tasks)
    oracle_cost = sum(min((cost(m, t) for m in models if solved(m, t)), default=0.0)
                      for t in tasks if any(solved(m, t) for m in models))

    short = lambda m: m.split("/")[-1]

    # enumerate cascades up to length 3 (cheap to brute force)
    cascades = []
    for r in (1, 2, 3):
        for order in itertools.permutations(models, r):
            res = eval_cascade(list(order))
            cascades.append((order, res))

    print(f"\n######## Stage 2: cost-cascade simulation ({len(tasks)} tasks, {len(models)} models) ########")
    print(f"\nbaseline (always best single = {short(best_model)}): "
          f"pass={base['pass']*100:.1f}%  cost=${base['cost']:.4f}  $/solved=${base['cps']:.4f}")
    print(f"oracle ceiling: pass={union_pass*100:.1f}%  cost=${oracle_cost:.4f}")

    # Pareto frontier (maximize pass, minimize cost)
    def dominated(a, others):
        return any(b["pass"] >= a["pass"] and b["cost"] <= a["cost"] and
                   (b["pass"] > a["pass"] or b["cost"] < a["cost"]) for _, b in others)
    pts = [(o, r) for o, r in cascades]
    pareto = [(o, r) for o, r in pts if not dominated(r, pts)]
    pareto.sort(key=lambda x: x[1]["cost"])

    print("\n--- Pareto-optimal cascades (cost vs pass) ---")
    print(f"{'pass':>7}{'cost$':>9}{'$/solv':>9}{'depth':>7}  cascade")
    for o, r in pareto:
        print(f"{r['pass']*100:>6.1f}%{r['cost']:>9.4f}{r['cps']:>9.4f}{r['mean_depth']:>7.2f}  "
              + " -> ".join(short(m) for m in o))

    # cheapest cascade that matches/beats the best single model's pass
    matches = [(o, r) for o, r in cascades if r["pass"] >= base["pass"] - 1e-9]
    best_cheap = min(matches, key=lambda x: x[1]["cost"])
    o, r = best_cheap
    save = (1 - r["cost"] / base["cost"]) * 100 if base["cost"] else 0

    # bootstrap CI on savings vs baseline for that cascade
    rng = random.Random(0); boots = []
    for _ in range(2000):
        samp = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        def c_cost(order, ts):
            tot = 0.0
            for t in ts:
                for m in order:
                    tot += cost(m, t)
                    if solved(m, t): break
            return tot
        bc = c_cost(o, samp); bb = c_cost([best_model], samp)
        boots.append((1 - bc / bb) * 100 if bb else 0)
    boots.sort(); lo, hi = boots[50], boots[1949]

    print("\n=== BEST COST ROUTER (cheapest cascade matching best-single quality) ===")
    print(f"  cascade : {' -> '.join(short(m) for m in o)}")
    print(f"  pass    : {r['pass']*100:.1f}%  (baseline {base['pass']*100:.1f}%)")
    print(f"  cost    : ${r['cost']:.4f}  vs baseline ${base['cost']:.4f}")
    print(f"  SAVINGS : {save:.0f}%  vs always-{short(best_model)}   95% CI [{lo:.0f}%, {hi:.0f}%]")
    print(f"  mean models called per task: {r['mean_depth']:.2f}")

    print("\n=== READ ===")
    if lo > 5:
        print(f"  Cost router captures real savings ({save:.0f}%, CI excludes ~0) at >= baseline quality.")
        print("  -> Cost-efficiency thesis HOLDS. Next: validate live (incl. tier-2-sees-failure)")
        print("     + benchmark vs OpenRouter Auto; widen N to tighten CIs.")
    else:
        print("  Realized savings are thin / CI ~includes 0 -> the oracle's -75% was mostly foresight;")
        print("  a verifier-gated cascade doesn't capture it here (premium needed too often).")
    print("\nNote: offline simulation from one-shot matrix; N small. Live confirmation needed.")


if __name__ == "__main__":
    main()
