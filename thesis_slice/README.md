# Ariadne — Thesis Slice ("Minimal Fugu")

A throwaway probe that answers one question before the real build:

> Does a multi-model collective (worker + a **separate** evaluator) solve coding
> tasks at least as well as a single strong model, at **lower or equal cost per
> solved task**?

See [`../THESIS_SLICE_SPEC.md`](../THESIS_SLICE_SPEC.md) for the full design and decision rule.

## Three arms

| Arm | What it is | Isolates |
|-----|-----------|----------|
| A0  | single model, one shot | raw single-model capability |
| A1  | single model, self-retry up to N | value of retries |
| B   | worker + separate evaluator (reflexion loop), up to N | value of a separate evaluator |

`(A1 − A0)` = value of retries. **`(B − A1)` = the thesis.**

## Setup

```bash
cd thesis_slice
python -m venv .venv && . .venv/Scripts/activate   # Windows; use .venv/bin/activate on *nix
pip install -r requirements.txt
cp .env.example .env        # then put your OpenRouter key in .env
```

## Run

```bash
python runner.py     # runs tasks x arms x trials, streams to results.jsonl, enforces budget
python report.py     # prints the decision table + GREENLIGHT / CONDITIONAL / KILL
```

Offline sanity check of the harness plumbing (no API spend):

```bash
python selftest.py
```

## Models (config.yaml)

- `single_model` = `deepseek/deepseek-v4-pro` — a strong, cheap coder => tough, honest baseline.
- `worker_model` = `qwen/qwen3-coder` — cheapest strong coder, drives B's cost edge.
- `evaluator_model` = `deepseek/deepseek-v4-pro` — same as baseline so `B vs A1`
  isolates the *separate-evaluator architecture*, not evaluator model quality.

Verify slugs against <https://openrouter.ai/models>; they change.

## Deliberate simplifications (do NOT carry into the real build)

- **Full-file rewrites**, not diffs (no patch engine yet).
- **Hand-crafted Python tasks**; only 2 ship here — gate 0 needs 8 (see `tasks/README.md`).
- **Caching is out of scope.** Its economics only matter at codebase scale (the
  cached Graphify static prefix); cached tokens are logged but not optimized.
- **Per-task budget is advisory**; only the per-run budget hard-stops.

These exist to make the probe cheap. The verdict, not the code, is the deliverable.
