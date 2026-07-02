# Ariadne — Security: Threat Model & OWASP Mapping

Design-time security posture for Ariadne. Written 2026-07-02, while the project is
**pre-production-code** — which is exactly when the cheap, high-leverage wins (OWASP
"Insecure Design") are available. Aligns with the gated build sequence in
[ARCHITECTURE.md](ARCHITECTURE.md) and the deployment tiers in [BUSINESS.md](BUSINESS.md).

---

## TL;DR

- Use **OWASP Top 10 for LLM Applications (2025)** as the *primary* lens; the classic
  **OWASP Top 10 (web, 2021)** as *secondary* for the HTTP endpoint.
- **Attack surface depends on deployment mode.** Self-host pushes most risk to the
  user; `pool_refresh` and the hosted tier put real risk on the operator.
- Near-term priorities: **cost-DoS / budget halting**, **BYOK key custody**, and
  **sandboxing the eval harness** (it runs untrusted model-generated code).
- Defer: model/data poisoning, embeddings, multi-tenant/RBAC, full pen-test — all
  premature or tied to features not yet built.
- Highest-value action *today*: this doc + a one-page threat model. A live audit is
  gated on code existing.

---

## Two OWASP lists, one spine

Ariadne is both an LLM application and an HTTP API/proxy, so both lists apply:
1. **OWASP LLM Top 10 (2025)** — primary. Ariadne is an LLM app.
2. **OWASP Web Top 10 (2021)** — secondary, for the exposed endpoint.

## Attack surface depends on deployment mode

The single most important framing — it maps onto the BUSINESS.md tiers:

| Mode | Who owns the trust boundary | Security burden |
|---|---|---|
| **OSS / self-host** | The user | Small: safe defaults, don't leak keys, enforce budget caps. Code execution happens on *their* machine. |
| **`pool_refresh` (operator)** | You | Real: runs **untrusted model-generated code** on your infra → sandboxing mandatory. |
| **Hosted Cloud tier** | You | Largest: multi-tenant isolation, auth, key custody, SSRF, cost-DoS all become yours. |

Deferring the hosted tier (per BUSINESS.md) is therefore also a **security
risk-deferral** — state it explicitly when sequencing the build.

## In scope (prioritized)

| # | Risk (OWASP) | Why it matters here | Mitigation |
|---|---|---|---|
| 1 | **Unbounded Consumption / Excessive Agency** (LLM10 / LLM06) | *The* headline risk for a BYOK escalation engine — a runaway cascade or a crafted prompt forcing max escalation drains a user's wallet. | Hard per-run budget cap (already in harness) + halting policy as a non-optional, first-class MVP feature; cap escalation depth. |
| 2 | **Sensitive Info Disclosure / Crypto Failures** (LLM02 / A02) | BYOK means handling users' provider keys. | Never persist or log raw keys; pass-through in memory; encrypt at rest if the hosted tier ever stores them. |
| 3 | **Injection / RCE + Improper Output Handling** (A03 / LLM05) | `pool_refresh` and `lang_sandbox.py` execute model-written code. | Existing controls (throwaway copies, reject edits outside declared solution files) + containerization, network-egress limits, CPU/mem/time caps. |
| 4 | **Prompt Injection** (LLM01) | Routing parses "did the last attempt fail?" from untrusted conversation text; content could fake pass (skip escalation) or force escalation (burn budget). | Keep the v1 router a *fixed policy*, not an LLM; treat the failure-detector as parsing untrusted input; sanity-check signals. |
| 5 | **Supply Chain / Data Integrity** (LLM03 / A06 / A08) | Distributed dependencies + the "Fresh Pool" config feed. | Pin deps with a lockfile; **sign/hash the Fresh Pool feed** so self-hosters can verify it. |
| 6 | **SSRF** (A10) | The pluggable transport adapter and leaderboard-scraping scout make outbound requests. | Allowlist provider hosts; forbid arbitrary injected base-URLs. |
| 7 | **Broken Access Control / Auth Failures** (A01 / A07) | Only when the hosted tier exists. | Standard API auth + per-tenant isolation — build with the hosted tier, not before. |
| 8 | **Logging & Monitoring Failures** (A09) | Where secret leaks actually happen. | Don't log prompts, user code, or keys; scrub before emitting. |

## Out of scope / deferred (and why)

- **Model & Data Poisoning (LLM04)** — no training in v1. Note: POOL_MANAGEMENT's
  "verifier elects the pool" design already resists *pool* poisoning via gamed
  leaderboards — a built-in mitigation worth documenting.
- **Vector / Embedding Weaknesses (LLM08)** — only relevant once Graphify (deferred)
  lands.
- **Classic SQL/ORM Injection (A03)** — likely no database early (stateless
  per-request); revisit if the hosted tier adds persistence.
- **Enterprise governance (RBAC, audit trails, DLP)** — defer to the Team/Pro tier;
  keep it out of the OSS core.
- **Full penetration test / live audit** — premature; there is no production code yet.

## Existing security-relevant controls (already in the harness)

- **Hard per-run budget cap** — the runner halts on spend, not the wallet.
- **Throwaway exercise copies** + **rejecting edits outside declared solution files** —
  model output can't tamper with tests or escape the task dir.
- **Hidden tests** — the generator never sees tests, only failing output.
- **Slug + key pre-flight checks** before any spend.

## Recommended next steps

1. **One-page threat model now** — data-flow diagram + STRIDE pass over: client →
   endpoint → transport adapter → provider, plus the `pool_refresh` path. Insecure
   Design is cheapest to fix before code exists.
2. **This `SECURITY.md`** — trust boundaries, in/out-of-scope Top-10 mapping,
   always-on controls (done).
3. **Bake always-on controls into the MVP spec:** budget/halting caps, no-secret-
   logging, dependency lockfile, signed Fresh Pool feed, host-allowlisted transport.
4. **Gate a real audit to code existence:** once the MVP endpoint exists, run the
   `/security` skill (OWASP Top 10 + AI threats) or the `security-auditor` subagent
   against it — and again before the hosted tier ships.

Net: **LLM Top 10 primary**, scope **per deployment mode**, prioritize **cost-DoS +
key custody + eval sandboxing** near-term, defer multi-tenant/governance with the
hosted tier.
