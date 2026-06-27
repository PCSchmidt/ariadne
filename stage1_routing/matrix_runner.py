"""Run the model x task capability matrix: each model alone, one attempt per task.
Streams one record per (model, task, trial) to matrix_results.jsonl."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml

from lang_sandbox import load_exercise, run_tests
from openrouter_client import OpenRouterClient
from task_select import select

ROOT = Path(__file__).parent


def _load_dotenv():
    for env in (ROOT / ".env", ROOT.parent / "thesis_slice" / ".env"):
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
            return


def _extract_files(text: str) -> Optional[Dict[str, str]]:
    t = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if fence:
        t = fence.group(1).strip()
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return None
    try:
        data = json.loads(t[s:e + 1])
    except Exception:  # noqa: BLE001
        return None
    files = data.get("files")
    if isinstance(files, dict) and all(isinstance(v, str) for v in files.values()):
        return files
    return None


def solve(client, cfg, model, ex):
    """One attempt (with JSON-repair retries). Returns (record_fields, files_or_None)."""
    paths = ", ".join(ex.solution_files.keys())
    sys_p = (f"You are an expert {ex.lang} programmer. Implement the solution so the "
             f"project's hidden test suite passes. Edit ONLY these files: {paths}. "
             f"Respond with ONLY a JSON object: "
             f'{{"files": {{"<path>": "<full file contents>"}}}}. '
             f"Include complete contents for each file. No tests, no prose.")
    user_p = [f"# Instructions\n{ex.instruction}", "# Files to implement (current stub)"]
    for rel, content in ex.solution_files.items():
        user_p.append(f"## {rel}\n```\n{content}\n```")
    messages = [{"role": "system", "content": sys_p},
                {"role": "user", "content": "\n\n".join(user_p)}]

    cost = inp = out = cached = 0
    latency = 0.0
    files = None
    repairs = 0
    for r in range(cfg["repair_retries"] + 1):
        call = client.chat(model, messages, temperature=cfg["temperature"],
                           json_mode=cfg["json_mode"], max_tokens=cfg["max_tokens"])
        cost += call.cost_usd; inp += call.input_tokens; out += call.output_tokens
        cached += call.cached_tokens; latency += call.latency_s
        files = _extract_files(call.content)
        if files is not None:
            break
        repairs += 1
        messages += [
            {"role": "assistant", "content": call.content[:2000]},
            {"role": "user", "content": 'That was not valid JSON of the required '
                                        'shape. Reply with ONLY {"files": {"<path>": '
                                        '"<full contents>"}} and nothing else.'},
        ]
    return {"cost_usd": cost, "input_tokens": inp, "output_tokens": out,
            "cached_tokens": cached, "latency_s": latency, "repairs": repairs}, files


def main():
    _load_dotenv()
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    chosen = select(cfg["languages"], cfg["n_per_lang"], cfg["seed"])
    client = OpenRouterClient()
    out_path = ROOT / "matrix_results.jsonl"
    run_budget = float(cfg["budget"]["per_run_usd"])
    run_cost = 0.0
    total = sum(len(v) for v in chosen.values()) * len(cfg["models"]) * cfg["trials"]
    done = 0

    with out_path.open("w", encoding="utf-8") as f:
        for lang, exs in chosen.items():
            for ex_path in exs:
                ex = load_exercise(lang, ex_path)
                for model in cfg["models"]:
                    for trial in range(cfg["trials"]):
                        done += 1
                        if run_cost >= run_budget:
                            print(f"[BUDGET] ${run_budget} reached; stopping.")
                            client.close(); return
                        err = ""
                        solved = False
                        rejected = []
                        try:
                            fields, files = solve(client, cfg, model, ex)
                            if files is None:
                                err = "no_valid_json_after_repairs"
                            else:
                                res = run_tests(ex, files)
                                solved = res.passed
                                rejected = res.rejected_edits
                        except Exception as e:  # noqa: BLE001
                            fields = {"cost_usd": 0, "input_tokens": 0, "output_tokens": 0,
                                      "cached_tokens": 0, "latency_s": 0.0, "repairs": 0}
                            err = f"{type(e).__name__}: {e}"[:120]
                        run_cost += fields["cost_usd"]
                        rec = {"model": model, "lang": lang, "task": ex.name,
                               "trial": trial, "solved": solved,
                               "rejected_edits": rejected, "error": err, **fields}
                        f.write(json.dumps(rec) + "\n"); f.flush()
                        short = model.split("/")[-1][:18]
                        print(f"[{done}/{total}] {lang:<6} {ex.name:<22} {short:<18} "
                              f"{'PASS' if solved else 'fail'} ${fields['cost_usd']:.4f}"
                              f"{('  '+err) if err else ''}")
    client.close()
    print(f"\nDone. Spend ${run_cost:.4f}. -> {out_path}\nRun: python analyze.py")


if __name__ == "__main__":
    main()
