# Ariadne — Direction: Capability vs. Cost Reframe

The pivotal course correction, in one place. Written 2026-07-01 from the evidence in
[FINDINGS.md](FINDINGS.md) and the offline cascade sim
([../stage1_routing/cascade_sim.py](../stage1_routing/cascade_sim.py)). For the
architecture that follows from this, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## TL;DR

- We aimed to build a **cost-efficient ("cheaper") Fugu**. The cost thesis is a
  **confirmed failure** — a realizable verifier-gated cascade saves **0%** vs. the
  best single model (95% CI [0%, 0%]).
- In its place the evidence revealed a **capability edge**: **+12.2 pts** task
  completion (73.2% → 85.4%) at **+33% cost/solved**, tunable down to **+6 pts for
  ~+11% cost**.
- Ariadne's identity shifted from **cost saver → capability amplifier with a
  quality/cost dial.**
- The moat is **execution-in-the-loop routing** (route *after* seeing test results),
  which prompt-time routers (e.g. OpenRouter Auto: 35.4% @ 3× cost) structurally
  cannot match.
- The trained Conductor/TRINITY router is **demoted to a later cost-optimizer**; the
  verifier captures ~92% of the headroom with zero training.

---

## Why the "cheaper Fugu" failed

The original falsifiable claim: *a routed collective delivers frontier quality at
lower cost/solved than any single frontier model.*

**The mirage.** The oracle (cheapest model that *happened* to solve each task) scores
86.6% at $1.09 vs. best-single 73.2% at $1.88 — looks like more quality for ~42% less
money.

**Why it evaporates.** The oracle needs *perfect foresight* (knowing which cheap
model will solve each task so you only pay that one). You can't have it at inference
time. The only realizable capture is a **verifier-gated cascade** (run model → run
tests → escalate on failure), and on every failure you pay for each model tried
*before* the one that works. That erases the savings.

**The structural lesson.** In a *fair* pool, cheap models aren't cheap enough at
*solving* to be a useful first tier — they fail often enough that you pay for them
*and then* pay the premium model anyway. A cost cascade only works when the pool
contains one overpriced model a cheap tier can undercut. That was exactly the v1
artifact (fake 28% savings, lopsided pool: 1 strong + 4 weak). Fair pool → savings
vanish:

| Pool iteration | Apparent cost savings |
|---|---|
| v1 (lopsided, N=30) | 28% (artifact of one overpriced model) |
| v2 (fair, N=30) | ~8%, 95% CI includes 0 |
| v3 (fair, N=82) | **0%, 95% CI [0%, 0%]** |

Killed for ~$24 total spend — the point of the probe.

## Why a low-cost trained Conductor/TRINITY was the wrong first move

1. **A trained router is a cost-optimizer, and there's no cost to optimize.** Its job
   is skipping doomed tiers; but the realizable cost floor already sits at the
   best-single price. Max recoverable = the escalation overhead on the quality tier,
   not a new economic category.
2. **You can't train it without first building the verifier.** The reward signal *is*
   the test outcome. You must build verifier-gated routing anyway to generate labels —
   and that already captures ~92% of headroom (85.4% of the 86.6% ceiling) with zero
   training. The trained router chases the last ~8%.
3. **Model churn poisons the investment.** The frontier pool turns over
   weekly-to-monthly (a *cheaper* model, qwen3.7-max, beat claude-sonnet-4.6 between
   revisions). A frozen policy decays; a test-gated cascade re-discovers the right
   model every run. This churn-resilience is developed in
   [POOL_MANAGEMENT.md](POOL_MANAGEMENT.md).
4. **The "separate evaluator" lever was the weakest one.** Probe 0 (worker + separate
   evaluator vs. self-retry) found nothing. The real lever is escalating to a
   *genuinely different model* on *verified* failure — cross-model diversity gated by
   an objective test, not intra-model self-critique.

## What we shifted to, and why it can win

**Capability amplifier**: an open-source, BYOK, OpenAI-compatible *agentic* endpoint
that picks the model per turn and escalates to a *different* model when the last
attempt failed its tests. The client already runs tests in its agent loop, so Ariadne
stays a stateless endpoint that just reads the last result and routes — the same shape
as Fugu, a small MVP. See [ARCHITECTURE.md](ARCHITECTURE.md).

### The quality/cost dial (Pareto frontier, v3 offline sim, 82 tasks)

You are not locked into +33%. The frontier gives explicit knobs:

| Cascade | Pass | $/solved | vs. best-single |
|---|---|---|---|
| qwen3.7-max (best single) | 73.2% | $0.0314 | baseline |
| qwen → claude | **79.3%** | $0.0347 | **+6.1 pts for +11% cost** |
| qwen → claude → glm | 81.7% | $0.0366 | +8.5 pts for +17% cost |
| qwen → claude → kimi | **85.4%** | $0.0418 | **+12.2 pts for +33% cost** |

`qwen → claude` is the sweet spot: +6 points for ~11% more money — a "quality mode"
no single model offers.

### The edge vs. the market

| Competitor | Result | Why Ariadne wins (or doesn't) |
|---|---|---|
| **Best single model** (the real bar) | 73.2% | +6 to +12.2 pts of completion via the dial; costs *more*, not less. |
| **OpenRouter Auto** (incumbent router) | 35.4% @ 3× cost/solved | Prompt-time routers pick a model *before* seeing execution → can't know what will succeed. The moat. |
| **Sakana Fugu** (closed leader) | proves the shape sells | Ariadne = open / self-hostable / BYOK / data-stays-local; no trained coordinator needed for v1. |

## Honest weaknesses of the edge

1. **Quality edge, not cost edge.** If the market wants "same quality, cheaper,"
   Ariadne has nothing.
2. **Everything rests on a verifier.** Coding-with-tests is the sweet spot; the
   no-verifier case (LLM-judge, compile/lint, model-generated tests) is unsolved and
   is the biggest risk.
3. **Offline + narrow.** 85.4% is a *simulation over independent one-shot attempts*,
   on one-shot polyglot puzzles — not a live cascade, not long-horizon agentic tasks,
   not real repos (where Fugu claims its biggest wins). Zero data there.
4. **Latency.** Escalation = sequential model calls; fine for CI, maybe painful
   interactively.
5. **N=82, one trial.** Tightened, not eliminated.

## Verdict & next gate

The **cost thesis is a documented failure** (preserve it — clean negative result).
The **capability thesis has a real, defensible on-paper edge** but its load-bearing
number (85.4%) has only existed *offline*. The last cheap falsification gate is a
**live cascade confirmation (~$2–4)**: run `qwen → claude → kimi` for real with tier-2
seeing tier-1's failure output (reflexion), on ~15–20 tasks. If it holds → build the
MVP endpoint. If it collapses → convert the project into a lessons-learned writeup.
Do not write endpoint code before this gate.

## See also

- [ARCHITECTURE.md](ARCHITECTURE.md) — the MVP shape + transport-agnostic design principle.
- [POOL_MANAGEMENT.md](POOL_MANAGEMENT.md) — model churn as an advantage; pool refresh + cost.
- [BUSINESS.md](BUSINESS.md) — open-core pricing, break-even, go-to-market sequence.
