# Ariadne — Pool Management & Model Churn

How Ariadne keeps its model pool current as the frontier turns over weekly, and why
leaderboards (e.g. [OpenRouter rankings](https://openrouter.ai/rankings#benchmarks))
are used only as a *scout*, never as the *judge*. Written 2026-07-01. Addresses
[ARCHITECTURE.md](ARCHITECTURE.md) Open Question #6 (pool maintenance). Depends on the
capability-vs-cost reframe in [DIRECTION.md](DIRECTION.md).

---

## TL;DR

- **Churn is Ariadne's comparative advantage, not its problem.** A trained router
  (Fugu) and a prompt-time router (OpenRouter Auto) both *decay* as models change —
  their "which model is best" belief goes stale. Ariadne routes on the **test outcome,
  re-evaluated every run**, so it adopts a better model the week it appears, with no
  retraining.
- The only place churn bites is **pool composition** (which N models are in the
  cascade, and in what order).
- **Rule: the leaderboard nominates candidates; your verifier elects the pool.**
  Never let a popularity/benchmark leaderboard select models directly — that is
  literally OpenRouter Auto, which we measured at 35.4% vs. our 85.4%.

---

## Why churn favors this architecture

| Architecture | How it encodes "best model" | Effect of weekly churn |
|---|---|---|
| Trained coordinator (Fugu Conductor/TRINITY) | Frozen weights | Asset decays; needs retraining. Pure liability. |
| Prompt-time router (OpenRouter Auto) | Stale priors, chosen before execution | Silent erosion; can't see the new model actually win. |
| **Ariadne (verify-and-escalate)** | **Nothing frozen — tests decide per run** | **Adopts better models immediately; policy is model-agnostic.** |

Inference-time routing is therefore the *least* churn-sensitive of the three. Churn is
reduced to a scheduled, bounded, automatable pool-refresh operation.

## Why the leaderboard is a scout, not a judge

OpenRouter's rankings are primarily a **usage / spend popularity** signal, not a
**capability-on-your-task** signal:

| Leaderboard signal | What it actually measures | Use for pool selection |
|---|---|---|
| Top Models (weekly tokens) | Popularity / momentum | Weak — popular ≠ best on your task |
| Top models by task (share of spend) | Popularity within a category | Moderate — narrows the field only |
| Market share by creator | Vendor concentration | Strategic context (supplier risk) only |
| Benchmarks tab | Synthetic scores | Contaminated + workload-mismatched |

Three structural defects of any public leaderboard/benchmark for this use:
1. **Popularity ≠ fitness** — confounded by price, free tiers, marketing, defaults.
2. **Contamination + workload mismatch** — frontier models train on public
   benchmarks; a SWE-bench leader may not lead on *your* distribution (we saw
   per-language specialization: Go→claude, Python→qwen, Rust→claude).
3. **Aggregation hides the tail** — Ariadne monetizes *uniquely-solved* tasks (9 of 82
   solved by only one model). Leaderboards rank by mean and hide exactly the diversity
   Ariadne exploits.

Reflexivity risk: if everyone selects pools by the same leaderboard, pools converge
and the routing headroom (the whole moat) collapses.

## SWOT — leaderboard-driven selection

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **S:** zero-cost, always-current candidate list; auto-surfaces new releases; price/context metadata aids cost-tier ordering | **W:** popularity ≠ pass-rate; blind to your verifier; averages away the unique-solve tail; confounded by price/hype |
| **External** | **O:** pair leaderboard (candidate gen) with a cheap private eval (selection); market "pool freshness" as a feature; use spend-share-by-task to pre-filter | **T:** over-reliance = become OpenRouter Auto; reflexive homogenization erases diversity; leaderboard gaming/API churn; vendor concentration shrinks real diversity |

## The mechanism: scout → judge

1. **Candidate generation (free, weekly).** Pull OpenRouter's coding/"Programming"
   task rankings + benchmark tab → shortlist ~8–12 plausible coding models, filtered
   by price and context ceilings you set. No spend.
2. **Selection (cheap, periodic — the Stage-1 matrix, re-run).** Run the shortlist
   against a **held-out, private eval set** (rotating Aider-polyglot slice + eventual
   dogfood tasks). This is the only signal that reflects *your* verifier. Elect pool
   members by pass-rate **and marginal unique-solve contribution** (does it solve tasks
   the current pool misses?), not by mean score.
3. **Ordering (derived).** Cascade order = cheapest-likely-first, from per-task
   pass-rate × **current** OpenRouter price (recompute prices at each refresh — they
   drift too).
4. **Cadence + cost control.** Full refresh ≈ Stage-1 spend (~$4–18 by N). Run
   **monthly, or event-triggered** on a major new coding entrant — not weekly.
5. **Canary (between refreshes).** Run each current pool model on 3–5 tasks to flag
   silent regressions or deprecations before they hit users.
6. **Guardrails.** Cap pool size (a new model must add ≥X unique solves to earn a slot
   — diminishing returns are fast; 4 models already reached 86.6% union in v3). Keep a
   **champion** you never drop without a challenger beating it. Preserve raw eval data
   per refresh for regression tracking (the experiments already do this).

## Cost to operate (estimates)

**Unit anchor (from real spend):** Stage 1 v3 cost $17.59 for 82 tasks × 5 models =
410 attempts → **~$0.04 per (model × task × trial)**, blended across cheap + premium
(includes the expensive `openrouter/auto`). Premium reasoning models run 2–4× that.
Planning formula: `cost = M models × N tasks × T trials × $0.04`. All figures are
**BYOK operator costs, paid once per refresh and amortized across all users** — one
refresh serves everyone until the next.

**Robustness drives cost, not cadence.** "Thorough" pushes T (trials, for variance —
v3 was 1-trial), N (tasks, for tighter CIs), and M (candidates) all up. Naive
`10×100×3 = 3,000 attempts ≈ $120/refresh` is wasteful because most models don't
change month to month.

**The cheap-but-robust design: two-stage funnel + incremental refresh.**

| Stage | Shape | Attempts | Cost |
|---|---|---|---|
| A — Screen (wide, 1 trial, small N) | 10 candidates × 30 × 1 | 300 | ~$12 |
| B — Confirm (finalists, 3 trials, full N) | top 5 × 100 × 3 | 1,500 | ~$60 |
| **Full refresh** | | 1,800 | **~$75** (range $75–130) |
| Incremental (steady state: re-eval only new/changed models vs frozen champions) | screen 3 + confirm 2 | ~690 | **~$28** |
| Canary (pool 4 × 5 tasks, weekly) | ~20/wk | | **~$40/yr** |

**Annualized tiers (GO/NO-GO envelope):**

| Tier | Cadence | Est. annual |
|---|---|---|
| Minimal | Quarterly full funnel + canary | ~$340/yr |
| **Recommended** | Monthly incremental + quarterly full + canary | **~$550/yr** |
| Heavy | Monthly full robust (10×100×3) + canary | ~$1,500/yr |

**Standing it up once ≈ $75–130; operating robustly ≈ $340–600/yr.** Cheap enough that
pool management is *not* the deciding cost variable — the still-unspent gates (live
cascade ~$2–4, then MVP build effort) dominate. GO on cost grounds.

**Budget guardrails (the one balloon risk is shortlist bloat × high N×T × premium
models at once → $200–400/refresh):**
1. **Hard per-run budget cap** (already in the runner) set to your ceiling — halts the
   run, not your wallet. A ~$600/yr hard cap buys the Recommended tier with margin.
2. **Two-stage funnel** — premium models never hit T=3/full-N unless they survive the
   cheap screen.
3. **Incremental-only steady state** — never re-pay for unchanged models.
4. **Pre-flight validation is $0** (local reference-solution runs).
5. Non-dollar cost: **rotating the private held-out eval set** (to prevent pool
   overfitting to a static task list) is labor, not spend; Aider-polyglot is a free
   starting corpus.

## The dominating caveat

Every step assumes a **verifier exists** to re-elect the pool. Where the workload is
coding-with-tests, churn is a solved, cheap, automatable operation. For no-verifier
workloads you are forced back onto leaderboards/benchmarks as the *only* selection
signal — i.e. back to being OpenRouter Auto, the regime where the edge disappears. The
churn-resilience story is strong *precisely and only* where the core thesis is strong.

## Concrete next step (added to ARCHITECTURE.md)

Build a **`pool_refresh`** routine (reuse `stage1_routing/` harnesses): leaderboard
scrape → shortlist → private-eval matrix → elect-by-unique-solve → emit ordered pool +
prices to `config.yaml`, plus a lightweight **canary** check. Schedule monthly /
event-triggered. This is post-MVP: it comes *after* the live cascade confirmation and
the MVP endpoint, but the design is fixed now so the MVP's pool config is shaped to
accept it.
