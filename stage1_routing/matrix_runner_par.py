"""Parallel matrix runner: same as matrix_runner but executes (model, task) cells
concurrently (cfg['workers']) so a widened pool finishes in ~1-2h not many hours.
Reuses solve()/_load_dotenv from matrix_runner; httpx.Client is thread-safe."""
from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

from lang_sandbox import load_exercise, run_tests
from matrix_runner import _load_dotenv, solve
from openrouter_client import OpenRouterClient
from task_select import select

ROOT = Path(__file__).parent


def main():
    _load_dotenv()
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    chosen = select(cfg["languages"], cfg["n_per_lang"], cfg["seed"])
    exercises = [load_exercise(lang, p) for lang, ps in chosen.items() for p in ps]
    cells = [(ex, m, t) for ex in exercises for m in cfg["models"] for t in range(cfg["trials"])]
    total = len(cells)

    client = OpenRouterClient()
    out_path = ROOT / "matrix_results.jsonl"
    run_budget = float(cfg["budget"]["per_run_usd"])
    workers = int(cfg.get("workers", 6))

    lock = threading.Lock()
    state = {"cost": 0.0, "done": 0, "stop": False}
    f = out_path.open("w", encoding="utf-8")

    def work(ex, model, trial):
        if state["stop"]:
            return
        err, solved, rejected = "", False, []
        try:
            fields, files = solve(client, cfg, model, ex)
            if files is None:
                err = "no_valid_json_after_repairs"
            else:
                res = run_tests(ex, files)
                solved, rejected = res.passed, res.rejected_edits
        except Exception as e:  # noqa: BLE001
            fields = {"cost_usd": 0, "input_tokens": 0, "output_tokens": 0,
                      "cached_tokens": 0, "latency_s": 0.0, "repairs": 0}
            err = f"{type(e).__name__}: {e}"[:120]
        rec = {"model": model, "lang": ex.lang, "task": ex.name, "trial": trial,
               "solved": solved, "rejected_edits": rejected, "error": err, **fields}
        with lock:
            f.write(json.dumps(rec) + "\n"); f.flush()
            state["cost"] += fields["cost_usd"]; state["done"] += 1
            d, c = state["done"], state["cost"]
            if c >= run_budget:
                state["stop"] = True
        print(f"[{d}/{total}] {ex.lang:<6} {ex.name:<20} {model.split('/')[-1]:<18} "
              f"{'PASS' if solved else 'fail'} ${fields['cost_usd']:.4f}"
              f"{('  ' + err) if err else ''}", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(work, ex, m, t) for ex, m, t in cells]
        for _ in as_completed(futs):
            pass
    f.close(); client.close()
    print(f"\nDone. Spend ${state['cost']:.4f}. -> {out_path}\nRun: python analyze.py")


if __name__ == "__main__":
    main()
