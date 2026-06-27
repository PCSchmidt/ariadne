# Ariadne — Experiments: Who / What / Where / When / How / Why

A high-level but detailed account of the experimental effort behind the findings.
For *results and interpretation* see [FINDINGS.md](FINDINGS.md); for the *current
plan* see [ARCHITECTURE.md](ARCHITECTURE.md). This document explains how the evidence
was produced and why it should be trusted (and where it shouldn't).

---

## The effort at a glance

| # | Experiment | When (2026) | Why (question) | Where (code) | Spend |
|---|---|---|---|---|---|
| 0 | Thesis slice | Jun 26 | Does a worker+evaluator beat a single model w/ self-retry? | [thesis_slice/](../thesis_slice/) | ~$0.28 |
| 1 | Routing-headroom matrix (v1/v2/v3) | Jun 26–27 | Does task→model routing beat the best single model? | [stage1_routing/](../stage1_routing/) | ~$23.6 |
| 2 | Verify-and-escalate cascade (offline) | Jun 27 | Is the routing headroom *realizable*, and at what cost? | [stage1_routing/cascade_sim.py](../stage1_routing/cascade_sim.py) | $0 |

Total ≈ **$24**, all bring-your-own-key spend.

---

## WHO

- **Operated by** an AI build agent (this Claude Code session) writing the harnesses,
  running them, and analyzing output, with **P.C. Schmidt (PCS)** directing every
  branch decision (task set, model pool, when to widen N, what to test next).
- **Compute:** the experiments themselves ran on **local Windows 11** hardware
  (Python 3.13, plus Go 1.19 / Rust 1.82 / Node / JDK toolchains for test execution).
- **Models:** accessed via **OpenRouter (BYOK)** — no model runs locally; OpenRouter
  brokers every frontier model call. Cost is the user's, hard-capped per run.

## WHY (the strategy)

The goal was to **confirm or kill the core bet cheaply before building anything.**
The guiding principles:

- **Falsifiable metrics.** Each experiment had a pre-declared number that, if unmet,
  would kill or redirect the thesis — not a vibe check.
- **Cheapest valid test first.** Spend the least to learn the most; escalate only when
  a result justifies it (Probe 0 → 30 tasks → 82 tasks).
- **Test the *most differentiated* claim.** After Probe 0 tested a weak mechanism, the
  effort pivoted to the crux: routing headroom (does any single model dominate?).
- **Instrument reliability before readings.** Bugs that corrupt measurement were fixed
  before trusting numbers (see "Controls").

## WHAT (each experiment)

### Probe 0 — Thesis slice
- **Tested:** three arms on hand-authored Python tasks — **A0** single model one-shot,
  **A1** single model with self-retry, **B** worker model + a *separate* evaluator
  model in a reflexion loop.
- **Done =** `pytest` exit 0. Tests **hidden from the generator** (only the failing
  output is fed back) so models can't hardcode answers.
- **Outcome:** inconclusive — tasks too easy (all arms ~100%; the evaluator never
  fired). Motivated the pivot to routing.

### Stage 1 — Routing-headroom matrix
- **Tested:** each model **alone, one attempt per task** — a pure capability matrix.
  No orchestration. From it we compute **best-single**, **oracle** (cheapest correct
  model per task), **union** (≥1 model solved), per-language winners, uniquely-solved
  counts, and the **gap = union − best-single** with bootstrap confidence intervals.
- **Three iterations**, each changing exactly one variable:
  - **v1** — 30 tasks, *lopsided* pool (1 strong + 4 weak). Flaw exposed: predetermined
    "no headroom."
  - **v2** — 30 tasks, *fair* pool (strong cheap coders + Claude). Verdict flipped.
  - **v3** — 82 tasks, fair pool, **+ `openrouter/auto` as a competitor baseline**,
    parallelized.
- **Done / metrics:** per (model, task): solved (bool), USD cost, tokens, latency.

### Stage 2 — Verify-and-escalate cascade (offline)
- **Tested:** cascade policies (ordered model tiers; try one, run tests, escalate on
  failure) **simulated from the Stage 1 matrix at $0** — a cascade is just a policy
  over already-recorded independent attempts.
- **Metrics:** realized pass rate, cost, $/solved, escalation depth, savings vs.
  best-single, all on the Pareto (cost vs. quality) frontier.

## WHERE (code, data, artifacts)

- **Harnesses:** `stage1_routing/` — `matrix_runner.py` / `matrix_runner_par.py`
  (the matrix), `lang_sandbox.py` (per-language test execution), `task_select.py`
  (stratified sampling), `analyze.py` (headroom verdict), `cascade_sim.py` (Stage 2),
  `openrouter_client.py` (BYOK API client). `thesis_slice/` holds Probe 0.
- **Task source:** Aider polyglot benchmark (cloned, gitignored) — Exercism exercises
  with hidden tests; `config.json` per exercise declares solution vs. test files.
- **Raw data (preserved, do not overwrite):**
  `matrix_results_v1_lopsided.jsonl`, `matrix_results_v2_strong.jsonl`, and the
  current `matrix_results.jsonl` (v3). One JSON line per (model, task, trial).
- **Config:** `stage1_routing/config.yaml` (models, languages, N, seed, budgets).

## WHEN

2026-06-26 (Probe 0, Stage 1 v1) through 2026-06-27 (Stage 1 v2/v3, Stage 2). A
two-day exploratory sprint.

## HOW (mechanics & controls)

**Execution loop (per matrix cell):**
1. Build a prompt: task instructions + the solution stub file(s); **tests withheld**.
2. Call the model via OpenRouter (BYOK), forcing a JSON `{"files": {...}}` response;
   on malformed output, **re-ask up to N times** (JSON-repair) before counting it a
   failure.
3. Write the returned file(s) into a **throwaway copy** of the exercise (edits outside
   the declared solution files are **rejected**, so tests can't be tampered with).
4. Run the language's test command (`pytest` / `go test` / `cargo test`); **exit 0 =
   solved**. Capture pass/fail, cost (from OpenRouter usage), tokens, latency.

**Controls that make the numbers trustworthy:**
- **Pre-flight validation** — every selected task's *reference solution* is run first
  to prove the toolchain works and the task is solvable (this caught a broken LRU test
  and Rust tasks needing external crates, which were excluded).
- **Slug + key checks** before any spend.
- **Stage 0 instrument fixes** — JSON-repair retries, higher `max_tokens`, UTF-8
  everywhere, and treating malformed output as retryable (after early runs were
  corrupted by truncation and a Windows encoding crash).
- **Deterministic sampling** (fixed seed) and **one changed variable per iteration**.
- **Bootstrap confidence intervals** over tasks — so "headroom" requires a CI that
  excludes zero, not a lucky point estimate.
- **Competitor & naive baselines** — `openrouter/auto` (existing router) and
  "always use the best single model" are the bars any routing must beat.
- **Hidden tests** — the generator never sees tests, only failing output.
- **Raw data preserved** per iteration for re-analysis.

**Known limits (carried in FINDINGS):** small N, one-shot (non-agentic) tasks,
coding-with-tests only, offline cascade (independent attempts), and a possibly-unfair
forced-JSON penalty on the competitor.

## Reproducing

See [stage1_routing/README.md](../stage1_routing/README.md). In short: clone the
polyglot benchmark, set an OpenRouter key, `validate_examples.py` (free sanity),
`matrix_runner_par.py`, then `analyze.py` and `cascade_sim.py`.
