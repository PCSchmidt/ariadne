# Ariadne — Architecture & Framework Proposition

Current proposition as of 2026-07-02, derived from the evidence in
[FINDINGS.md](FINDINGS.md) and the reframe in [DIRECTION.md](DIRECTION.md). This is a
*proposition*, not built yet; open questions are listed at the end and several could
still change the shape. Related: pool/model-churn strategy in
[POOL_MANAGEMENT.md](POOL_MANAGEMENT.md); market & pricing in [BUSINESS.md](BUSINESS.md).

---

## What Ariadne is

An **open-source, BYOK, OpenAI-compatible *agentic* endpoint** that routes each turn
of a coding task to the model most likely to advance it, and **escalates to a
different model when the previous attempt fails its tests**. It is consumed by
existing agent CLIs (Codex, Claude Code, Cursor) the same way Sakana Fugu is — the
client points at Ariadne's base URL instead of a single provider.

It is a **capability amplifier**: it reaches task-completion rates no single model in
the pool achieves alone (~85% vs. ~73% best-single in our benchmark).

## Why an *agentic* endpoint, not a routing proxy

The headroom is only realizable by seeing execution results — a prompt-time router
(e.g. OpenRouter Auto) can't, and scored worse than every model in our pool. But
Ariadne does **not** need to run tests itself. In an agent loop, the *client* already
executes code and feeds results (test output, stack traces) back into the
conversation. So:

```text
turn 1:  client → Ariadne → [model A] proposes patch
         client runs tests locally → FAIL → appends output to conversation
turn 2:  client → Ariadne → Ariadne sees turn-1 failed → routes to [model B]
         client runs tests → PASS → done
```

Ariadne's job each turn: **read the conversation state (including the last execution
result) and choose the model for this turn**, switching models when the prior attempt
failed. This realizes verify-and-escalate *within the standard agentic protocol*,
keeping Ariadne a stateless-per-request, OpenAI-compatible endpoint.

## Components (MVP → later)

**MVP (validated path):**
1. **OpenAI-compatible endpoint** (chat completions; ideally Responses too) with a
   BYOK pass-through, via a **pluggable transport adapter** (default OpenRouter; also
   LiteLLM / platform-native gateways). See *Design principle: transport-agnostic*.
2. **Turn router:** a policy that reads conversation history and picks the model.
   v1 policy = a fixed escalation order (e.g. `qwen3.7-max → claude → kimi`),
   advancing when the last turn shows a failed verifier. *No training required.*
3. **Failure signal extraction:** detect "previous attempt failed" from the
   conversation (test output, non-zero exits, error blocks) to trigger escalation.
4. **Model pool config + cost/quality dial:** ordered tiers, budget caps, the
   Pareto knob (how far to escalate).

**Design principle: transport-agnostic (MVP decision).** Ariadne is not a gateway/router
(OpenRouter, LiteLLM, Portkey, Cloudflare/Vercel) — it is a **verify-and-escalate layer
that sits *on top* of one**. So the provider transport is a **pluggable adapter from
day one**, not hard-wired to OpenRouter. Consequences: (a) hedges OpenRouter's fee (5.5%)
and latency-hop vulnerability — and the fee is noise inside a +33% quality envelope
anyway, while the *latency* hop compounds escalation latency and is the real thing to
minimize; (b) enables a fully self-hosted **Ariadne + LiteLLM = data-never-leaves-your-box**
story, a sharper open/self-hostable wedge vs. Fugu; (c) lets Ariadne **compose with** the
governance tier (LiteLLM/OpenRouter/Ariadne stacked) instead of being squeezed by it.
The main competitive watch-item is a governance gateway (Portkey/Kong) bolting on
escalation — but they route at *prompt time* and can't see execution results, so the
moat holds. The candidate-generation scout (see POOL_MANAGEMENT) should likewise pull
from multiple gateway catalogs + public benchmarks, not OpenRouter's leaderboard alone.

**Later / optional (deferred per findings):**
- **Trained router** (TRINITY-style classifier / Conductor-style generator) — a cost
  optimizer that *predicts* the right model to skip wasted tiers; only worth it once
  the verifier-gated baseline is proven and we need to cut the +33% cost.
- **Graphify** context layer — codebase knowledge graph as a cached static prefix for
  repo-scale tasks.
- **Meridian** gates / generator-evaluator — re-homed as the **verifier for tasks
  without tests** (LLM-judge), and as governance for long-horizon runs.

## Relationship to the four influences (re-prioritized)

| Influence | Role now | Why |
|---|---|---|
| Verification / Meridian evaluator | **Core** | Escalation must be gated by a verifier; it *is* the router. |
| Conductor / TRINITY (trained) | **Later optimizer** | Tests capture ~92% of headroom without training. |
| Graphify (context graph) | **Deferred layer** | Needed for repo-scale cost/context, not for the core value. |
| Differential memory / recursive topologies | **Deferred** | MVP needs only per-turn selection + escalation. |

## Competitive position

- **vs. Sakana Fugu:** same shape (agentic endpoint, consumed by an agent CLI), but
  Fugu is closed/hosted with a trained coordinator and your data goes to Sakana.
  Ariadne is open, self-hostable, BYOK, data-stays-local — and needs no trained
  coordinator for v1.
- **vs. OpenRouter Auto / prompt-time routers:** structurally can't run your tests, so
  can't capture the headroom (measured: 35% vs our 85%). This is the moat.
- **vs. "just use the best single model" (qwen3.7-max):** any router must beat
  best-single, not the premium model. Verify-and-escalate does (85% vs 73%).

## Open questions / hurdles (could change the shape)

1. **No-verifier tasks.** The value rests on a verifier. For tasks without tests,
   explore: model-generated tests, compile/lint/type-check as weak verifiers, or an
   LLM-judge evaluator (Meridian). How well does escalation work on a noisy verifier?
2. **Latency.** Escalation = multiple sequential model calls. Acceptable for
   autonomous/CI use; possibly painful for interactive use. Mitigations: speculative
   parallel attempts, cheap-first ordering, a predictor to skip tiers.
3. **Cost.** Quality costs more (+33%/solved at full escalation). Expose a
   quality/cost dial; consider a trained predictor to avoid doomed cheap attempts.
4. **Where does execution live?** Leaning on the client's existing agent loop (like
   Fugu/Codex). If a target client doesn't loop with execution, Ariadne may need its
   own thin agent/sandbox mode — a heavier build to evaluate.
5. **Generalization.** Confirm on long-horizon agentic tasks and real repos before
   committing; one-shot polyglot is a narrow slice.
6. **Pool management.** Frontier models churn weekly; the ordered tiers and verifier
   thresholds need a maintenance/refresh process (Fugu advertises exactly this as a
   feature). Resolved in [POOL_MANAGEMENT.md](POOL_MANAGEMENT.md): churn is actually a
   comparative advantage here (tests re-elect the best model every run — nothing
   frozen decays), and the leaderboard is used only as a *scout* for candidates while
   a private verifier eval *elects* the pool. Never select models directly from a
   popularity/benchmark leaderboard — that is OpenRouter Auto (35% vs. our 85%).

## Immediate next steps (proposed)

1. **Live cascade confirmation** (~$2–4): run `qwen3.7-max → claude → kimi` live with
   real escalation-*with-failure-context* on ~15–20 tasks; confirm the offline 85%
   holds and whether reflexion improves it.
2. **MVP endpoint**: OpenAI-compatible proxy + turn router + failure detection, point
   Codex/Claude Code at it, dogfood on a real change.
3. **`pool_refresh` routine** (post-MVP; design fixed now, see
   [POOL_MANAGEMENT.md](POOL_MANAGEMENT.md)): reuse `stage1_routing/` harnesses to
   scrape the OpenRouter coding leaderboard → shortlist → private-eval matrix →
   elect-by-unique-solve → emit an ordered pool + current prices to `config.yaml`,
   plus a lightweight **canary** (3–5 tasks/model between refreshes to catch silent
   regressions/deprecations). Run monthly or event-triggered on a major new coding
   entrant. Shape the MVP's pool config now to accept this.
4. Then revisit the deferred layers (predictor, Graphify, no-verifier verification)
   based on where dogfooding hurts.

The go-to-market track (OSS release → Fresh Pool feed → hosted Cloud tier) runs in
parallel and is gated on the same live-cascade confirmation — see [BUSINESS.md](BUSINESS.md).
