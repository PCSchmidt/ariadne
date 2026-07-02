# Ariadne

> A thread through the labyrinth of large-model software engineering — an open,
> verify-and-escalate orchestrator that amplifies coding capability beyond any single
> model.

**Status: design + validation (as of 2026-07-02).** The core bet has been tested
with real experiments and **confirmed**, but with an important course correction
(see below). No production code yet — the repo holds the brainstorm, the experiment
harnesses, the findings, and the strategy docs (direction, pool management, business)
that now drive the build.

---

## The one-paragraph version

No single LLM is best at every coding task. Ariadne is an open-source,
bring-your-own-key orchestrator that routes work across a pool of frontier models
and — crucially — **runs the tests and escalates to a *different* model when one
fails**. On a fair benchmark, this verify-and-escalate loop reaches ~85% task
completion where the best single model reaches ~73%, and it does so *without a
trained router* — the tests do the routing. It is the open, self-hostable analog of
Sakana's (closed, hosted) Fugu, with a sharper, evidence-backed identity: a
**capability amplifier**, not a cost saver.

---

## Genesis: where this came from

Ariadne started in a graduate AI-engineering course, from a simple observation:
**no single AI model is the best at everything.** Ask five top models to write the
same piece of code and they'll succeed and fail on *different* problems. So what if,
instead of betting on one model, you had something that picked the right model for
each job — and, when a model got it wrong, quietly handed the work to a different one
until it was right?

A useful mental picture: think of a **general contractor**. You don't hire the
plumber to do the wiring. A good contractor knows which specialist to call for each
part of the job, checks their work, and brings in someone else if it isn't done
right. Ariadne is a general contractor for AI models: it sends your task to a capable
model, lets your tools *check the result*, and escalates to a different model when the
check fails. The checking is the secret — it's what lets Ariadne beat any single
model instead of just guessing.

This idea isn't invented from scratch. It builds on two 2026 research papers from
[Sakana AI](https://sakana.ai/), which also power Sakana's own (closed, paid)
product, [**Fugu**](https://sakana.ai/fugu/):

- **[TRINITY: An Evolved LLM Coordinator](https://arxiv.org/abs/2512.04695)** — shows
  that a tiny, cheap "coordinator" can hand a task to a pool of larger models turn by
  turn, giving each a role (plan it, do it, or check it), and that this *team* of
  models reliably outperforms any single one — across coding, math, and reasoning.
- **[Learning to Orchestrate Agents in Natural Language with the Conductor](https://arxiv.org/abs/2512.04388)**
  — shows that a model can *learn* how to route work and write tailored instructions
  for each specialist, even discovering when to try again with a corrected plan after
  a failure. It's the "how do you coordinate the team well" half of the picture.

Sakana's Fugu turns these ideas into a hosted, closed product. **Ariadne is the open,
self-hostable, bring-your-own-key take on the same insight** — and, guided by our own
experiments, a deliberately simpler one: we found that *letting your tests do the
routing* captures most of the benefit without needing a trained coordinator at all.

### Who it's for

- **Developers** — plug Ariadne into the coding assistant you already use (Claude
  Code, Cursor, Codex) and get more tasks actually completed, because a failed attempt
  gets a second, *different* model instead of the same one trying again.
- **Hobbyists & tinkerers** — it's open source and BYOK: run it yourself, use your own
  API keys, keep your code on your own machine, no subscription and no vendor lock-in.
- **Creators & learners** — the whole project (including the experiments and the
  honest record of what *didn't* work) is public, so you can read it, learn from it,
  fork it, or build on it.

---

## Why this exists

**The one-line reframe:** we set out to build a *cheaper* Fugu and the evidence
killed the cost angle — but revealed a *capability* edge in its place. A realizable
verifier-gated cascade saves **0%** over the best single model (the "oracle" savings
need perfect foresight you can't have at inference time), so Ariadne is **not** a
cost saver. What it *is* is a **capability amplifier with a quality/cost dial**: on a
fair 82-task benchmark it lifts task completion from **73.2% → 85.4% (+12.2 pts)** at
**+33% cost/solved** — and you can turn the dial down to **+6 pts for only ~+11%
cost** (`qwen → claude`). You pay a little more to solve tasks no single model in the
pool can. The moat is that this edge is only reachable by **routing *after* seeing
test results**, which prompt-time routers structurally cannot do. Full detail:
[docs/DIRECTION.md](docs/DIRECTION.md).

- **No model dominates.** Different frontier models win different task types; we
  measured a real +13-point gap between the best single model and a perfect
  task→model router (95% CI excludes zero).
- **Prompt-time routers can't capture it.** OpenRouter's own Auto router scored
  *worse than every model in the pool* on our benchmark, because a router that only
  reads the prompt can't know which model will actually succeed. The headroom is
  only realizable by **closing the loop with execution** — generate, run the
  verifier, escalate on failure. That is Ariadne's defensible wedge.
- **The closed leader proves the shape.** Sakana Fugu ships exactly this idea as a
  hosted, *closed*, trained-coordinator product behind an OpenAI-compatible
  endpoint consumed by an agent CLI. Ariadne occupies the open / self-hostable /
  BYOK / data-stays-local whitespace.

## The core idea (current)

```text
agentic client (Codex / Claude Code / Cursor)  ──►  Ariadne endpoint
   │  proposes change                                  │  picks a model for THIS turn
   │  runs tests locally (as agent loops do)           │  reads prior turn's results
   ◄── feeds results back ──────────────────────────── ◄  escalates to a DIFFERENT
                                                           model when the last attempt
                                                           failed its tests
```

Ariadne is an **OpenAI-compatible, *agentic* endpoint**. Within a normal multi-turn
agent loop (where the client already executes code and feeds results back), Ariadne
chooses *which model handles each turn* and switches models when the conversation
shows the previous attempt failed. The client runs the tests; Ariadne reads the
outcome and routes. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## What we set out to test, and what we found

The full record is in [docs/FINDINGS.md](docs/FINDINGS.md). Headlines:

| Question | Finding |
|---|---|
| Does multi-model routing beat the best single model? | **Yes.** Best single 73.2% vs. oracle 86.6% (+13.4 pts, 95% CI [+6.1, +22.0]) on 82 Aider-polyglot tasks across Python/Go/Rust. |
| Is the prize cost or quality? | **Quality.** A verify-and-escalate cascade reaches 85.4% (~92% of the ceiling) but at *higher* cost (+33%/solved). The "cheaper Fugu" cost angle is dead; capability amplification is the real prize. |
| Do we need a trained router (TRINITY/Conductor)? | **Not for v1.** Tests do the routing. A trained router is a later cost-optimizer, not the core. |
| Can the existing router (OpenRouter Auto) already do this? | **No.** It scored 35.4% at 3× the cost-per-solved — it can't run your tests. |
| Is a cheaper model competitive with the premium one? | **Yes.** `qwen3.7-max` (73.2%, ~$1.25/Mtok) beat `claude-sonnet-4.6` (65.9%, $3/Mtok). |

## The four influences, reframed by the evidence

The project began by synthesizing four ideas (see
[InitialScopeBrainstorming.md](InitialScopeBrainstorming.md)). The findings sharply
re-prioritized them:

- **Conductor / TRINITY** (trained orchestrators) — *demoted.* The verifier, not a
  trained model, captures most of the value. Training becomes a later optimization.
- **Verification / generator-evaluator split ([Meridian](https://github.com/PCSchmidt/meridian))** —
  *promoted to the core.* Escalation must be gated by a verifier; the open question is
  what serves as the verifier when there are no tests (see Open Questions).
- **Graphify** (codebase knowledge graph) — *deferred.* A context/cost layer for
  codebase-scale work, not needed to prove or realize the core value.
- **Differential memory / recursive topologies** — *deferred.* The MVP is far
  simpler than the original grand architecture.

### What is Meridian, and why it helps here

[**Meridian**](https://github.com/PCSchmidt/meridian) is a companion open-source
project: a **governance harness for AI agents** that stops them from marking broken
work as "done." Its three ideas matter for Ariadne:

- **A separate evaluator** — the agent writing the code is never the one that judges
  it ("the generator can't praise its own work"). This is exactly the *verifier* that
  gates Ariadne's escalation, and the natural answer for tasks that have **no tests**
  (an LLM-judge stands in for a test suite).
- **Enforced gates + halting** — work advances only after each step is checked, with a
  hard cap on retries before it bubbles up to the human. That's Ariadne's budget/
  depth limit and a key safety control against runaway cost.
- **Reflexion memory** — a failure is compressed into a short lesson (not a raw dump
  of broken code) and carried forward, so the *next* model escalated to learns from
  the last one's mistake.

Ariadne won't swallow Meridian wholesale — it borrows these patterns **incrementally**,
each when the milestone needs it (reflexion at the live-cascade test, halting at MVP,
the evaluator-as-verifier for no-test tasks, and full gates only for long, multi-step
jobs). See the staged plan in
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#meridian-integration-staged-by-pattern--not-a-wholesale-dependency).

## Open questions / hurdles (actively being explored)

1. **The no-verifier case.** The whole value rests on a verifier. Coding-with-tests
   is the sweet spot; many real tasks lack tests. Options to explore:
   model-generated tests, compile/lint/type-check as weak verifiers, or an LLM-judge
   evaluator (this is where Meridian's evaluator earns its place).
2. **Latency.** A cascade is multiple sequential model calls — a real cost for
   interactive use.
3. **Cost positioning.** Quality costs more; the quality/cost dial is now quantified
   (see [docs/DIRECTION.md](docs/DIRECTION.md) — e.g. +6 pts for ~+11% cost up to
   +12.2 pts for +33%). Still open: a cheap predictor to skip tiers unlikely to succeed.
4. **Generalization.** Validated on one-shot polyglot coding tasks; not yet on
   long-horizon agentic tasks or real repos (where Fugu claims its biggest wins).
5. **Fair competitor test.** Some of OpenRouter Auto's poor score may be
   forced-JSON format artifacts; worth a cleaner re-test.

*Resolved / addressed since:* **model churn & pool selection** →
[docs/POOL_MANAGEMENT.md](docs/POOL_MANAGEMENT.md); **transport lock-in / gateway
competition** → transport-agnostic adapter in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md);
**monetization & pricing** → [docs/BUSINESS.md](docs/BUSINESS.md).

## Repository map

| Path | What |
|---|---|
| [README.md](README.md) | This overview |
| [docs/DIRECTION.md](docs/DIRECTION.md) | The capability-vs-cost reframe, the quality/cost Pareto dial, and market edge |
| [docs/POOL_MANAGEMENT.md](docs/POOL_MANAGEMENT.md) | How model churn is handled; leaderboard-as-scout vs. verifier-as-judge; pool_refresh + canary |
| [docs/BUSINESS.md](docs/BUSINESS.md) | Market analysis, open-core pricing, Fresh Pool feed, break-even, go-to-market sequence |
| [docs/SECURITY.md](docs/SECURITY.md) | Threat model + OWASP LLM/Web Top-10 mapping; per-deployment-mode trust boundaries; in/out-of-scope |
| [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) | Who/what/where/when/how/why of every experiment + methodology & controls |
| [docs/FINDINGS.md](docs/FINDINGS.md) | The experiment log (v1→v2→v3), numbers, and what each taught us |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current architecture/framework proposition + open questions |
| [InitialScopeBrainstorming.md](InitialScopeBrainstorming.md) | Origin conversation (historical) |
| [ScratchNotesBrainstorming.txt](ScratchNotesBrainstorming.txt) | Early Q&A notes (historical) |
| [THESIS_SLICE_SPEC.md](THESIS_SLICE_SPEC.md) | First experiment spec (**superseded** — see banner) |
| [thesis_slice/](thesis_slice/) | First probe: single vs. worker+evaluator (superseded by Stage 1) |
| [stage1_routing/](stage1_routing/) | The routing-matrix + cascade experiments that produced the findings |

## Reproducing the experiments

```bash
cd stage1_routing
pip install -r requirements.txt
git clone --depth 1 https://github.com/Aider-AI/polyglot-benchmark   # task source (gitignored)
# put an OpenRouter key in .env (or ../thesis_slice/.env)
python validate_examples.py    # toolchain + task sanity (no spend)
python matrix_runner_par.py    # the model x task capability matrix
python analyze.py              # headroom verdict + competitor comparison
python cascade_sim.py          # verify-and-escalate cascade (offline, $0)
```

## Origins & name

Ariadne grew out of a research conversation on agentic coding and orchestration
([InitialScopeBrainstorming.md](InitialScopeBrainstorming.md)), with Sakana's Fugu
as the north star. In myth, Ariadne's thread led Theseus out of the labyrinth; large
codebases are labyrinths where models get lost. Ariadne is the thread.
