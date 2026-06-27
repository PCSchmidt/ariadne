# Ariadne — Findings & Experiment Log

A running record of what we tested, what we learned, and how the plan changed.
Newest understanding at the top of each section. Dates absolute.

---

## TL;DR (as of 2026-06-27)

1. **Routing headroom is real.** On 82 Aider-polyglot coding tasks (Python/Go/Rust)
   across a fair pool of frontier models, a perfect task→model router beats the best
   single model by **+13.4 points** (86.6% vs 73.2%), 95% CI **[+6.1, +22.0]** —
   excludes zero.
2. **The prize is quality, not cost.** A verify-and-escalate cascade captures ~92%
   of that headroom (reaches 85.4%) **without a trained router**, but at *higher*
   cost (+33%/solved). The original "cost-efficient Fugu" thesis is dead; the
   realistic identity is a **capability amplifier**.
3. **The differentiator is execution-in-the-loop.** OpenRouter's Auto router scored
   35.4% (3× cost/solved) — a prompt-time router can't run your tests, so it can't
   capture the headroom. Verify-and-escalate can.
4. **No trained coordinator needed for v1.** Tests do the routing. TRINITY/Conductor
   become a later optimization, not the core.

---

## Course corrections vs. the original brainstorm

Reviewing [InitialScopeBrainstorming.md](../InitialScopeBrainstorming.md),
[ScratchNotesBrainstorming.txt](../ScratchNotesBrainstorming.txt), and
[THESIS_SLICE_SPEC.md](../THESIS_SLICE_SPEC.md) against the evidence:

| Original assumption | Status | What changed |
|---|---|---|
| "Open-source, **cost-efficient** Fugu" | **Revised** | Cost savings are unrealizable (oracle's −42% needs perfect foresight). The prize is **quality amplification**. |
| Core engine = **trained** Conductor/TRINITY router | **Demoted** | A verifier-gated cascade captures ~92% of headroom with *zero* training. Trained routing is a later cost-optimizer. |
| Grand architecture (differential memory, recursive topologies, Graphify ontology, Meridian DAG) | **Deferred** | MVP is far simpler: per-turn model selection that escalates on verified failure. |
| Win comes from a **separate evaluator vs. self-retry** (the thesis-slice framing) | **Superseded** | The lever is escalating to a *different model* on verified failure (cross-model diversity + verification), not single-model self-evaluation. |
| Routing across many models beats one | **Confirmed** | +13.4 pts, CI excludes zero. |
| BYOK via OpenRouter | **Confirmed sound** | But OpenRouter's own Auto router is a weak competitor; our edge is verification-in-the-loop. |
| Meridian's generator/evaluator split | **Re-homed** | Its real role is as the **verifier** when objective tests are absent. |

This is a healthy change of course: the project is *simpler and more defensible*
than the brainstorm imagined (no trained coordinator required for v1), with a
clearer identity (capability, not cost) and a concrete moat (execution-gated
routing that prompt-time routers structurally cannot match).

---

## Experiment timeline

### Probe 0 — Thesis slice (single vs. worker+evaluator)
*Dir: [thesis_slice/](../thesis_slice/). Superseded.*

First probe: does a worker + separate evaluator (reflexion loop) beat a single model
with self-retry, on small Python tasks? **Inconclusive** — the tasks were too easy
(all arms ~100%, the evaluator loop never fired) and results were contaminated by
harness bugs (JSON truncation, Windows encoding). Lesson: it tested the *least
differentiated* mechanism on a saturated regime. This motivated the pivot to a
proper routing-headroom experiment on a discriminating benchmark.

### Stage 1 — Routing-headroom matrix
*Dir: [stage1_routing/](../stage1_routing/). Each model runs alone, one attempt per
task; from the matrix we compute best-single, oracle (cheapest correct per task),
union (≥1 model solved), per-language winners, and uniquely-solved counts.*

**v1 — lopsided pool (30 tasks).** Pool: claude-sonnet-4.6 + four *weak* cheap
models (gpt-oss-120b, qwen3-coder, glm-4.5-air, deepseek-v4-pro). Claude dominated
(63%, best in every language); gap +6.7 pts, CI **[0, +16.7]** (includes zero).
*Flaw:* one strong vs. four weak models predetermined "no headroom." A cheap-cascade
looked like it saved 28% — but that was an artifact of one expensive model the cheap
tier could undercut.

**v2 — fair strong pool (30 tasks).** Pool corrected per OpenRouter coding rankings:
mimo-v2.5-pro, deepseek-v4-pro, kimi-k2.7-code, glm-5.2, qwen3.7-max,
claude-sonnet-4.6. Result **flipped**:
- A *cheaper* model won: **qwen3.7-max 76.7% > claude 66.7%**, at <½ the price.
- **Specialization appeared:** best model differed by language.
- Gap +10 pts, CI **[0, +23]** (still includes zero at N=30).
- Cost-cascade savings collapsed to ~8% (CI includes 0) — the v1 28% was an artifact.

**v3 — widen N + competitor (82 tasks).** Dropped mimo/deepseek (0 unique solves),
added `openrouter/auto`. Parallel runner (6 workers). $17.59.

| model | pass | $/solved |
|---|---|---|
| qwen3.7-max | 73.2% | $0.0314 |
| claude-sonnet-4.6 | 65.9% | $0.0321 |
| kimi-k2.7-code | 64.6% | $0.0659 |
| glm-5.2 | 50.0% | $0.0354 |
| openrouter/auto (competitor) | 35.4% | $0.1073 |

- **best single** qwen3.7-max 73.2% @ $1.88; **union/oracle** 86.6% @ $1.09.
- **gap +13.4 pts, 95% CI [+6.1, +22.0] — excludes zero.** Headroom confirmed.
- per-language best: go→claude (63%), python→qwen3.7-max (77%), rust→claude (82%);
  9 tasks uniquely solved across all four models.
- **openrouter/auto demolished:** 35.4% at 3× cost/solved.

### Stage 2 (offline) — Verify-and-escalate cascade
*[stage1_routing/cascade_sim.py](../stage1_routing/cascade_sim.py), simulated from the
v3 matrix at $0 (a cascade is a policy over recorded independent attempts).*

- `qwen3.7-max → claude → kimi-k2.7-code` reaches **85.4%** (~92% of the 86.6%
  ceiling) — **no trained router**, the tests gate escalation.
- It costs **more**, not less (+33%/solved). Confirms: **quality amplification, not
  cost savings.** The Pareto frontier is a genuine quality/cost dial.

---

## Caveats / threats to validity

- **Verifier dependency.** Every result assumes a test/verifier exists. Generalizing
  to no-test tasks is an open question (see ARCHITECTURE → Open Questions).
- **Offline cascade.** cascade_sim uses *independent* one-shot attempts; a live
  cascade where tier-2 sees tier-1's failure (reflexion) is untested and may do
  better/cheaper.
- **Scope.** One-shot polyglot coding only; long-horizon agentic tasks and real
  repos untested (where Fugu claims its largest wins).
- **Competitor fairness.** Some of Auto's poor score may be forced-JSON format
  artifacts; a cleaner re-test is warranted.
- **N.** 82 tasks tightens but does not eliminate uncertainty; widen before heavy
  investment.

## Cost ledger (experiments)

Probe 0 ≈ $0.28 · Stage 1 v1 $0.06 · re-run (broken) $0 · v1-proper $1.40 · v2
$4.53 · v3 $17.59. Cascade analyses $0 (offline). Total ≈ **$24**.
