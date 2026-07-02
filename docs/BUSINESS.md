# Ariadne — Business: Market, Pricing & Go-to-Market

Draft monetization model for Ariadne as an open-source project with a paid turnkey
tier. Written 2026-07-02. Depends on the capability-vs-cost reframe
([DIRECTION.md](DIRECTION.md)) and the pool-refresh operating cost
([POOL_MANAGEMENT.md](POOL_MANAGEMENT.md)). Sequencing aligns with the prove-then-build
gates in [ARCHITECTURE.md](ARCHITECTURE.md). All prices illustrative.

---

## TL;DR

- **BYOK means you cannot sell tokens** (that's OpenRouter's model). The paid tier sells
  **convenience + pool freshness + support**, not compute.
- Model = **open-core (Apache-2.0) + managed hosting**, the LiteLLM shape.
- Sell the thing that costs you money: the **monthly pool refresh** becomes the paid
  feature — bundled in the hosted tier and sold standalone as a **"Fresh Pool" feed**.
- **Cost-recuperation floor ≈ $55–70/mo**; break-even ≈ **4–5 hosted users** or **~12
  Fresh Pool subscribers**.
- Portfolio-first: the **working monetization loop is the deliverable**, not ARR.
  Optimize for a clean, demonstrable, cost-covering loop.

---

## The pricing reality: BYOK

Because Ariadne is bring-your-own-key, it is structurally barred from cost-plus token
resale. The paid tier sells exactly three things:
1. **Convenience** — turnkey hosting, zero setup, dashboard, the cost/quality dial as UI.
2. **Freshness** — the managed monthly pool refresh (the recurring cost + labor).
3. **Support/trust** — reliability, updates, someone to email.

This is standard **open-core + managed-hosting**. Do NOT resell tokens for a "single
bill" — that drops Ariadne into OpenRouter's fee-squeeze war, which it currently sits
above.

## Market analysis

**Category comps (WTP anchors):**

| Product | Price | Relevance |
|---|---|---|
| GitHub Copilot | $10/mo | Devs pay ~$10 for coding help reflexively |
| Cursor | $20/mo | ~$20/mo individual dev-tool ceiling |
| LiteLLM | OSS + enterprise (contact-us) | Closest structural analog (OSS proxy + paid tier) |
| Sakana Fugu | Closed/hosted, enterprise | Ariadne's differentiator: open, self-hostable, cheaper entry |
| OpenRouter Auto | ~free | The "good enough for free" floor Ariadne must out-perform |

**Segments:**

| Segment | Pays for | WTP |
|---|---|---|
| Tinkerer / OSS dev | Nothing — they are stars + credibility | $0 |
| Indie/prosumer dev | Hosted turnkey + fresh pool | ~$10–20/mo |
| Small team | Seats, shared config, analytics, support | ~$50–150/mo |
| Enterprise | Governance, SLA, audit | High but expensive to serve — don't chase yet |

**Honest read:** a niche layered tool, not a mass product. Buyers = devs who already
use agentic coding tools, feel the +12-pt completion lift, and won't self-host. Revenue
potential is modest; the **demonstration is the primary asset**. Biggest market risk:
the lift isn't *felt* enough to beat "OpenRouter Auto is free" inertia — which is why the
live cascade confirmation gates everything.

## Monetization structure

**License:** **Apache-2.0** on the core — maximizes adoption/stars (portfolio value),
signals confidence, matches infra-tooling norms. Reach for source-available (BSL/Elastic)
only if fearing a cloud giant reselling the hosted tier — overkill here and it dampens
stars.

**Tiers:**

| Tier | What | Price (illustrative) | Purpose |
|---|---|---|---|
| **OSS / Self-host** | Full engine, BYOK, run your own pool_refresh | $0 | Adoption, stars, portfolio proof |
| **Fresh Pool feed** | Monthly-benchmarked, ready-to-drop-in `config.yaml` pool + ordering + current prices | ~$5/mo or $49/yr | Monetizes self-hosters; lowest-risk first product |
| **Ariadne Cloud** (individual) | Hosted endpoint, zero setup, dashboard, dial UI, managed pool refresh | ~$15/mo or $144/yr | Cost recuperation |
| **Team/Pro** (later) | Seats, shared config, usage analytics, priority support | ~$59–99/mo | Upside — build only on demand |

## The clever bit: sell the thing that costs you money

The one recurring operator cost is **pool_refresh (~$550/yr + labor)**. Make it the paid
feature. Run the benchmark once, sell the output twice:
1. **Bundled** into Ariadne Cloud (hosted users get fresh pools automatically).
2. **Standalone Fresh Pool feed** for self-hosters who want the OSS engine without
   spending $550/yr + labor benchmarking models. Marginal cost ~zero (already run).

Defensible one-liner: "models benchmarked on real coding tasks with a verifier, not a
popularity leaderboard" — nobody else offers this. Directly ties revenue to the cost
that must be recouped.

## Cost-recuperation floor / break-even

| Item | Est. |
|---|---|
| Endpoint hosting (thin stateless proxy — Fly/Railway/serverless) | $5–20/mo |
| Pool refresh (amortized ~$550/yr) | ~$46/mo |
| Domain + Stripe fees | ~$5/mo + 2.9%/txn |
| **Fixed floor** | **~$55–70/mo** |

- **Break-even at $15/mo:** ~4–5 paying users.
- **Break-even on the $5/mo feed:** ~12–14 subscribers.
- **Rule:** don't turn on hosting until ~3 committed users or a Sponsors base covers the
  floor — otherwise the hosted tier bleeds before it earns.
- **Pre-revenue bridge:** GitHub Sponsors / founding-supporter tier from day one;
  sponsorware (early Fresh Pool access) covers pool_refresh with zero hosting liability.

## Portfolio-specific guidance

The monetization **design + execution is itself the artifact** — it shows you can build
OSS, design open-core pricing, instrument it, and land real users. So:
- Optimize for a clean, credible, cost-covering loop over max ARR. $100/mo from 8 real
  users proves more than a projection.
- **Instrument everything** (conversion, activation, churn) even at tiny scale.
- **Build-in-the-open narrative** — the DIRECTION.md honesty (killed the cost thesis,
  pivoted to capability) is rare, rigorous, compelling portfolio content.

## Go-to-market sequence (gated, prove-then-build)

1. **Live cascade confirmation** (~$2–4) — pricing power is downstream of this result.
2. **OSS release** (Apache-2.0) + README/landing page → collect stars & Sponsors.
3. **Fresh Pool feed** — cheapest paid product, near-zero infra, monetizes self-hosters.
4. **Ariadne Cloud** hosted tier — only if there is demonstrated pull. Don't build the
   billing/hosting stack before the core value is proven and wanted.
5. **Team/Pro** — only on inbound demand.

## Risks to pricing

1. **Strong free floor** — OpenRouter Auto is free; the lift must be *felt*. WTP depends
   on the live-cascade result.
2. **Two-bill friction** — BYOK = user's token bill + your fee. Keep the fee low, framed
   as "the intelligence layer." Don't resell tokens.
3. **Solo-founder support/uptime load** — a hosted tier is a commitment; the Fresh Pool
   feed has almost none. Prefer it first.
4. **Value-metric mismatch** — flat subscription is simplest; revisit per-task pricing
   only if uneven per-user value demands it.

## Net recommendation

Apache-2.0 open-core; free self-host; a **$5/mo Fresh Pool feed** as the first, lowest-
risk paid product (monetizes the exact cost to recoup); a **~$15/mo hosted Cloud tier**
added only once there's demand; GitHub Sponsors bridging from day one. Break-even ~4–5
hosted users or ~12 feed subscribers. For a portfolio, a working monetization loop that
cleanly covers costs is the win.
