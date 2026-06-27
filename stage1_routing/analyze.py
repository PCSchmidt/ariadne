"""Compute the routing-headroom verdict from matrix_results.jsonl.

Base models define union/oracle/best-single. Any model in ROUTERS (e.g.
openrouter/auto) is a *competing router*, not a base model -- it's excluded from
the union/oracle and reported separately against best-single and the oracle.

  best-single : highest pass-rate BASE model (bar to beat)
  union/oracle: tasks solved by >=1 base model (ceiling for any router)
  gap         : union - best-single (max prize), with 95% bootstrap CI
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
INF = float("inf")
ROUTERS = {"openrouter/auto"}


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
    if not (ROOT / "matrix_results.jsonl").exists():
        print("No matrix_results.jsonl."); return
    agg = load()
    all_models = sorted({k[0] for k in agg})
    base = [m for m in all_models if m not in ROUTERS]
    routers = [m for m in all_models if m in ROUTERS]
    tasks = sorted({(k[1], k[2]) for k in agg})
    langs = sorted({t[0] for t in tasks})
    short = lambda m: m.split("/")[-1]

    def solved(m, t): return agg.get((m,) + t, {"solved": False})["solved"]
    def cost(m, t): return agg.get((m,) + t, {"cost": 0.0})["cost"]

    print(f"\n######## Routing Matrix — {len(base)} base + {len(routers)} router, {len(tasks)} tasks ########\n")
    hdr = f"{'model':<28}{'pass':>7}{'solved':>8}{'cost$':>9}{'$/solved':>11}"
    print(hdr); print("-" * len(hdr))
    pass_rate = {}
    for m in all_models:
        s = sum(solved(m, t) for t in tasks)
        c = sum(cost(m, t) for t in tasks)
        pass_rate[m] = s / len(tasks)
        tag = "  [router]" if m in ROUTERS else ""
        cps = f"{c/s:.4f}" if s else "n/a"
        print(f"{m:<28}{s/len(tasks)*100:>6.1f}%{s:>8}{c:>9.4f}{cps:>11}{tag}")

    best_model = max(base, key=lambda m: pass_rate[m])
    best_pass = pass_rate[best_model]
    best_cost = sum(cost(best_model, t) for t in tasks)

    union = [t for t in tasks if any(solved(m, t) for m in base)]
    union_pass = len(union) / len(tasks)
    oracle_cost = sum(min((cost(m, t) for m in base if solved(m, t)), default=0.0) for t in union)
    gap = union_pass - best_pass

    print("\n--- best BASE model per language (specialization signal) ---")
    lang_best = {}
    for lg in langs:
        lt = [t for t in tasks if t[0] == lg]
        sc = {m: sum(solved(m, t) for t in lt) / len(lt) for m in base}
        bm = max(base, key=lambda m: sc[m]); lang_best[lg] = bm
        u = sum(any(solved(m, t) for m in base) for t in lt) / len(lt)
        print(f"  {lg:<8} -> {short(bm):<20} ({sc[bm]*100:.0f}%)   union={u*100:.0f}%")
    routes_differ = len(set(lang_best.values())) > 1

    print("\n--- uniquely solved among base models ---")
    uniq = defaultdict(int)
    for t in tasks:
        sv = [m for m in base if solved(m, t)]
        if len(sv) == 1:
            uniq[sv[0]] += 1
    for m in base:
        if uniq[m]:
            print(f"  {short(m):<22} {uniq[m]}")

    # bootstrap CI on gap
    rng = random.Random(0); boots = []
    for _ in range(2000):
        samp = [tasks[rng.randrange(len(tasks))] for _ in tasks]
        bp = sum(solved(best_model, t) for t in samp) / len(samp)
        up = sum(any(solved(m, t) for m in base) for t in samp) / len(samp)
        boots.append(up - bp)
    boots.sort(); lo, hi = boots[50], boots[1949]

    print("\n=== ROUTING HEADROOM (base models) ===")
    print(f"  best single : {short(best_model)}  pass={best_pass*100:.1f}%  cost=${best_cost:.4f}")
    print(f"  union/oracle: pass={union_pass*100:.1f}%  oracle_cost=${oracle_cost:.4f}")
    print(f"  GAP         : {gap*100:+.1f} pts   95% CI [{lo*100:+.1f}, {hi*100:+.1f}]")

    if routers:
        print("\n=== COMPETITOR: openrouter/auto vs base ===")
        for m in routers:
            s = sum(solved(m, t) for t in tasks); c = sum(cost(m, t) for t in tasks)
            print(f"  {short(m)}: pass={pass_rate[m]*100:.1f}%  cost=${c:.4f}  "
                  f"$/solved=${c/s:.4f}" if s else f"  {short(m)}: 0 solved")
            print(f"    vs best-single {short(best_model)} ({best_pass*100:.1f}% @ ${best_cost:.4f}); "
                  f"vs oracle ceiling ({union_pass*100:.1f}% @ ${oracle_cost:.4f})")

    print("\n=== VERDICT ===")
    drivers = []
    if lo > 0.05:
        drivers.append(f"capability gap real (CI low {lo*100:+.1f} > 5)")
    if routes_differ:
        drivers.append("best model differs by language")
    if best_cost and oracle_cost < 0.8 * best_cost:
        drivers.append("oracle materially cheaper")
    if lo > 0.05 and routes_differ:
        print("  HEADROOM CONFIRMED -> predictive routing worth building (if it beats auto + best-single).")
    elif drivers:
        print("  HEADROOM SUGGESTIVE but not confirmed. Drivers:")
        for d in drivers: print(f"    - {d}")
    else:
        print("  NO MEANINGFUL HEADROOM -> single best model ~dominates; reconsider routing thesis.")
    for d in drivers:
        print(f"    - {d}")


if __name__ == "__main__":
    main()
