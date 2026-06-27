# Ariadne — Thesis Slice Spec ("Minimal Fugu")

> **⚠ SUPERSEDED (2026-06-27).** This was the *first* probe (single model vs.
> worker+evaluator on easy Python tasks). It proved inconclusive — the tasks were too
> easy to fire the evaluator loop — and motivated the pivot to a proper
> routing-headroom experiment. Current direction and evidence:
> [docs/FINDINGS.md](docs/FINDINGS.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
> Kept as a historical record of the reasoning.

Status: design · Owner: PCS · Goal: cheaply confirm or kill the core bet before building the full orchestrator.

## 1. Hypothesis (falsifiable)

> On a fixed set of coding tasks, a **multi-model collective** (a worker model + a *separate* evaluator model in a reflexion loop) solves at least as many tasks as a **single strong model** given the same attempt budget, at **lower or equal dollar cost per solved task**.

If the collective cannot beat a single model per dollar on this probe, the "cheaper Fugu" thesis is wrong or needs reframing — and we learn it in a weekend, not a quarter.

## 2. Decision rule (write the verdict before running)

Let `pass@N` = fraction of tasks solved within N attempts; `$/solved` = total spend / tasks solved.

- **GREENLIGHT** if `B.pass@N ≥ A1.pass@N` **and** `B.$/solved ≤ A1.$/solved`.
  (Collective is at least as capable and no more expensive per result.)
- **CONDITIONAL** if B solves *more* tasks than A1 but at higher `$/solved` — record the premium; revisit once routing/caching is tuned.
- **KILL / RETHINK** if B costs more per solved task with **no** capability gain.

This is a go/no-go *probe* (N≈8 tasks), not a benchmark paper. It produces signal, not proof.

## 3. Three arms (isolate the variable)

Comparing single vs. collective alone confounds "second model" with "more compute/attempts." So three arms:

| Arm | Description | Isolates |
|-----|-------------|----------|
| **A0** | Single model, **one shot**. Generate → run tests. | Raw single-model capability. |
| **A1** | Single model, **self-retry** up to N. Feeds its own test failure back to itself (self-reflexion). | Value of retries / more compute. |
| **B**  | **Worker** model generates → **separate evaluator** model reviews diff + test output, emits a reflexion → worker revises. Up to N attempts. | Value of a *separate* evaluator (the generator/evaluator split). |

Read-off: `A1 − A0` = value of retries. `B − A1` = value of a separate evaluator model. The thesis lives in `B − A1`.

## 4. Eval set (gate 0)

Build this **first**; the harness is meaningless without it.

- **v0: 8 hand-crafted Python tasks.** Self-contained, function/small-module scope. Each = a folder with:
  - `task.md` — natural-language instruction.
  - source file(s) with a missing/broken implementation.
  - `test_*.py` — currently failing; **"done" = `pytest` exits 0**.
  - `meta.yaml` — allowed-edit file list, difficulty tag.
- **Credibility upgrade (later, not in v0):** swap/add a few [SWE-bench Lite] instances once the harness works.
- Keep tasks **private/novel** to reduce training-data contamination. Vary difficulty (trivial → multi-file).

## 5. Metrics (logged per task × arm × trial)

- `solved` (bool), `attempts_used`
- tokens: `input`, `output`, `cached` (per model call)
- `cost_usd` (from OpenRouter response usage)
- `latency_s`
- Aggregate: `pass@N`, total cost, `$/solved`, mean attempts, and **variance across trials**.

## 6. Harness architecture (minimal — no TUI, no Graphify, no DAG, no git)

```
thesis_slice/
  tasks/                # the eval set (§4)
  openrouter_client.py  # httpx wrapper: chat call, session_id sticky header, parse usage+cost
  schemas.py            # Pydantic: WorkerOutput(files:{path:contents}), EvalVerdict(passed:bool, reflexion:str)
  arms.py               # arm_a0, arm_a1, arm_b  -> returns Trajectory(solved, attempts, calls[])
  sandbox.py            # copy task dir to temp, write model files, run pytest via subprocess, capture exit+stdout
  runner.py             # loops tasks × arms × trials, enforces budgets, writes results.jsonl
  report.py             # reads results.jsonl, prints the §2 decision table
  config.yaml           # model slugs, N, budgets, trials, temperature
```

**Edit application = full-file rewrite, not diffs.** Model returns complete contents for files in the allowed-edit list; harness writes them and runs tests. Avoids building a patch/diff engine in the probe. (Known simplification — note for later.)

**Flow per attempt (Arm B):**
1. Worker call → `WorkerOutput` (files). Write to sandbox copy.
2. Run pytest. If pass → solved, stop.
3. Evaluator call: sees `task.md` + the diff + pytest stdout → `EvalVerdict(passed, reflexion)`.
4. Append `reflexion` to working context (append-only). Loop to 1 until pass or N reached.

## 7. Config defaults

- `N = 3` attempts. `trials = 3` per task (fix `temperature` low/0 but repeat to estimate variance).
- Budgets (hard caps, kill on breach): `$0.50/task`, `$15/full-run`.
- Models — **configurable slugs**, swap to current OpenRouter offerings:
  - A0/A1 single: one strong coder.
  - B worker: cheaper strong coder; B evaluator: strong reasoner (different family from worker).
- One fixed `session_id` per arm-run to keep prompt caching warm; record `cached` tokens.

## 8. Validity threats & mitigations

- **Tiny N (8 tasks):** report per-task results, not just aggregate; treat as signal.
- **Selection bias** in hand-crafted tasks: mix difficulties; add SWE-bench later.
- **Nondeterminism:** fixed temperature + 3 trials/task; report variance.
- **Contamination:** keep tasks novel/private.
- **Evaluator/worker correlation:** use different model families for worker vs. evaluator.
- **Caching is secondary here:** real cache economics appear at *codebase* scale (the cached Graphify static prefix), which this probe does not test. Record cache tokens but do not optimize; the caching-vs-routing economics is a **separate follow-up probe**.

## 9. Build milestones (order, ~weekend)

1. `tasks/` — 8 tasks with failing tests. (gate 0)
2. `sandbox.py` — copy-dir + write-files + run-pytest + capture. Test it standalone.
3. `openrouter_client.py` — one real call, confirm usage/cost + cached-token fields parse.
4. `schemas.py` + `arms.py` — A0 first (simplest), then A1, then B.
5. `runner.py` + budgets + `results.jsonl`.
6. `report.py` — print the §2 table. Run it. Read the verdict.

## 10. Definition of done (for the slice)

Harness runs all tasks × 3 arms × 3 trials under budget, emits `results.jsonl` and a printed decision table, and the §2 rule yields GREENLIGHT / CONDITIONAL / KILL. Throwaway-quality code is acceptable — this exists to answer one question.
