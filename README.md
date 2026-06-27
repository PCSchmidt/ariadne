# Ariadne

> A thread through the labyrinth of large-model software engineering — an open,
> verify-and-escalate router that amplifies coding capability beyond any single model.

**Status: design + validation (as of 2026-06-27).** The core bet has been tested
with real experiments and **confirmed**, but with an important course correction
(see below). No production code yet — the repo currently holds the brainstorm, the
experiment harnesses, and the findings that now drive the build.

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

## Why this exists

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
- **Verification / generator-evaluator split (Meridian)** — *promoted to the core.*
  Escalation must be gated by a verifier; the open question is what serves as the
  verifier when there are no tests (see Open Questions).
- **Graphify** (codebase knowledge graph) — *deferred.* A context/cost layer for
  codebase-scale work, not needed to prove or realize the core value.
- **Differential memory / recursive topologies** — *deferred.* The MVP is far
  simpler than the original grand architecture.

## Open questions / hurdles (actively being explored)

1. **The no-verifier case.** The whole value rests on a verifier. Coding-with-tests
   is the sweet spot; many real tasks lack tests. Options to explore:
   model-generated tests, compile/lint/type-check as weak verifiers, or an LLM-judge
   evaluator (this is where Meridian's evaluator earns its place).
2. **Latency.** A cascade is multiple sequential model calls — a real cost for
   interactive use.
3. **Cost positioning.** Quality costs more; Ariadne needs an explicit quality/cost
   dial, and possibly a cheap predictor to skip tiers unlikely to succeed.
4. **Generalization.** Validated on one-shot polyglot coding tasks; not yet on
   long-horizon agentic tasks or real repos (where Fugu claims its biggest wins).
5. **Fair competitor test.** Some of OpenRouter Auto's poor score may be
   forced-JSON format artifacts; worth a cleaner re-test.

## Repository map

| Path | What |
|---|---|
| [README.md](README.md) | This overview |
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
