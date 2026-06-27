# Stage 1 — Routing Headroom

The crux experiment: **does any single model dominate, or does matching task -> model
beat the best single model?** If there's no headroom, the multi-model orchestrator
has no reason to exist and the project should pivot to the augmenter shape.

This runs **each model alone, one attempt, on every task** — a pure capability
matrix. No conductor, no evaluator, no orchestration. From that one matrix we read
the ceiling of what routing could ever buy.

## What it measures

- **best-single** — highest pass-rate model (the bar to beat).
- **union / oracle** — tasks solved by >= 1 model (ceiling for any router).
- **gap = union - best-single** — the maximum prize routing could capture (with 95% bootstrap CI).
- **oracle cost** — cheapest correct model per task (the cost prize).
- **best model per language** — if the winner changes by language, routing has value even if the overall union is close.
- **uniquely solved** — tasks only one model got.

## Task set

Stratified sample from [Aider polyglot](https://github.com/Aider-AI/polyglot-benchmark):
`n_per_lang` exercises each in **Python, Go, Rust** (native `pytest` / `go test` /
`cargo test`). Java/C++/JS deferred (no gradle, old g++, per-exercise npm installs)
— add later via Docker if headroom is confirmed.

## Run

```bash
cd stage1_routing
pip install -r requirements.txt
git clone --depth 1 https://github.com/Aider-AI/polyglot-benchmark   # task source (gitignored)
python validate_examples.py   # pre-flight: toolchains + tasks sound (no API spend)
python matrix_runner.py       # the matrix (uses OPENROUTER_API_KEY; reads ../thesis_slice/.env too)
python analyze.py             # headroom verdict
```

## Models

Chosen for spread across labs and price tiers (see `config.yaml`) — there must be
diversity or there is nothing to route between. Verify slugs at
<https://openrouter.ai/models>.

## What this does NOT test

Whether a *real* router can capture the headroom (Stage 2), the evaluator/reflexion
loop (Stage 3), or codebase-scale caching (Stage 4). Stage 1 only bounds the prize.
