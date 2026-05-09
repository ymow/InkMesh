# ACR-200｜Cross-Covenant Reputation
## Agent Reputation Across Covenants · v0.1-DRAFT · May 2026

> ⚠️ **SPECULATIVE — gating remains.**
>
> Per `ACP_Roadmap.md` v0.4.3 §Phase 5: this work is gated on Phase 7.A
> (Escrow + Auto-Settlement) completing first AND producing real-
> transaction data. Reputation built on synthetic Covenants is noise.
>
> This v0.1 draft exists so the design space is in writing, not so the
> work can begin. Implementation is forbidden until both gates clear.

---

## Provenance

| | |
|---|---|
| Status | DRAFT — awaiting Phase 7.A real-tx data |
| Authors | working group |
| Last update | 2026-05-09 |
| Implementation gate | Phase 7.A complete + ≥30 real settled Covenants with real money |
| Numbering | ACR-200 (gap between ACR-100 settlement and ACR-300 audit) |

---

## What problem this solves (and what it doesn't)

**Problem:** an agent walking up to a new Covenant has no reputational
context. Owners must rely on `self_declaration` (ACR-50 §2.2) plus
their own due-diligence. There's no way to ask "has this agent
demonstrated reliability across other Covenants on this server, or
across federated servers?"

**Not the problem:** identity verification, sybil resistance, collusion
detection. ACR-200 measures **observed performance**, not **identity
trustworthiness**. Sybil-resistant identity is a separate workstream
(out of scope, possibly ACR-800+).

**Why this is gated on Phase 7.A:** without escrow-backed real-money
settlement, "reputation" is just an inflated participation count. The
roadmap is explicit: reputation built before Escrow is "noise". The
metric needs financial skin-in-the-game to be meaningful.

---

## Core concepts

### Agent Reputation Score (ARS)

A per-agent integer 0–10000 (basis points × 100) computed from settled
Covenant outcomes.

```
ARS = floor(10000 × weighted_acceptance × completion_factor × consistency_factor)
```

Where:

- `weighted_acceptance` (0–1): sum of `acceptance_ratio × tier_multiplier × token_amount` across all settled Covenants where the agent participated, divided by the same sum if all had been accepted at acceptance_ratio=1.0.
- `completion_factor` (0–1): fraction of Covenants joined that reached SETTLED (not abandoned by the agent leaving early).
- `consistency_factor` (0–1): standard deviation penalty — agents whose acceptance_ratio is highly variable across Covenants score lower than agents with consistent quality.

ARS is **not** transitive across operators — each acp-server computes
its own view. Federated reputation (Section 5) is opt-in cross-server
queries.

### Tier auto-upgrade (per Phase 5 roadmap)

Owners may opt into auto-upgrade rules at Covenant creation:
`autotier_above_ars = 7500` means "an agent with ARS ≥ 7500 can submit
passages at one tier higher than they were configured for, capped at
the highest configured tier."

Disabled by default. Reputation is a *signal*, not a *replacement* for
the owner's tier-curation authority.

### Covenant Registry (discovery surface)

Server-side table listing all Covenants the operator has created OR
syndicated to. Optionally publishable as a `.well-known/acp-covenants`
JSON endpoint so other servers can query.

Discovery is opt-in. The default for a self-hosted server is
"completely private — only members can see Covenants." Operators flip
specific Covenants public when they want inbound contributors.

### Cross-server query (federated reputation)

A standardised endpoint:

```
GET /acp/agents/{platform_id_hash}/reputation
```

returns the queried server's view of an agent's ARS plus a list of
publicly-known settled Covenants. Servers MAY refuse to answer (rate
limits, privacy settings, hostility detection); answers MAY include
only public-Covenant participation.

Aggregating ARS across federated servers is **client-side**, not
server-side. Each acp-server holds its own view; aggregating views
into a single global score is a client/UI concern (and politically
fraught, deliberately deferred).

---

## Schema additions (informative)

```sql
CREATE TABLE agent_reputation (
    server_id       TEXT NOT NULL,                       -- this server's id (for federation)
    platform_id_hash TEXT NOT NULL,                       -- ACR-700 platform_id_hash
    ars             INTEGER NOT NULL DEFAULT 0,           -- 0..10000
    weighted_acceptance REAL,
    completion_factor REAL,
    consistency_factor REAL,
    settled_covenants_count INTEGER NOT NULL DEFAULT 0,
    last_recomputed_at DATETIME,
    PRIMARY KEY (server_id, platform_id_hash)
);

CREATE TABLE covenant_registry (
    covenant_id     TEXT PRIMARY KEY REFERENCES covenants(id),
    visibility      TEXT NOT NULL DEFAULT 'private'
                    CHECK(visibility IN ('private','members','public','federated')),
    summary         TEXT,                                  -- short pitch for discovery
    listed_at       DATETIME
);

CREATE TABLE federated_servers (
    server_id       TEXT PRIMARY KEY,                      -- another acp-server's id
    base_url        TEXT NOT NULL,
    pubkey          TEXT NOT NULL,                          -- for federated query auth
    trusted_at      DATETIME NOT NULL,
    last_synced_at  DATETIME
);
```

---

## Open questions (DRAFT will not answer these without real-tx data)

| # | Question | Why it depends on real-tx data |
|---|---|---|
| R-1 | Is `weighted_acceptance` the right primary signal, or is `unique-Covenants-completed` more meaningful? | Need to see whether high-acceptance agents are also high-stakes agents or whether they cluster in low-tier work |
| R-2 | What's the right `consistency_factor` shape? Current draft uses standard deviation; could be IQR | Real distribution of acceptance ratios needed to pick a robust statistic |
| R-3 | Should ARS decay over time? | Without real data we can't tell whether old reputation is still predictive |
| R-4 | What's the cold-start treatment for new agents? Current draft: ARS=0 until 3 settled Covenants. Should the threshold be different? | Need to see how many newcomers vs returning agents we have |
| R-5 | Federation: who is allowed to query whom? Whitelist? Public? Friends-of-friends? | Adversarial pressure unknown without real adoption |
| R-6 | Is ARS public to other agents in a Covenant, or owner-only? | Privacy expectations differ wildly between OSS and enterprise |
| R-7 | Penalty for `leave_covenant` mid-flight: how heavy? | Constitutional Principle 5 says leaving is a right; reputation systems often punish it. Tension unresolved without seeing how often it happens with real money on the line |
| R-8 | When an agent's ARS changes mid-Covenant, does that affect already-submitted-but-unapproved passages? | Need to see whether owners want this or find it disruptive |

---

## Path to ratification

```
1. Phase 7.A ships. Real escrow settlements begin.
2. After ≥30 settled Covenants with real money, snapshot the data.
3. Working group analyses: what would ARS have predicted? Were
   acceptance ratios actually consistent within agents?
4. R-1..R-8 answered with evidence (and may surface new questions).
5. ACR-200 v0.2 written from real data.
6. Reference implementation in acp-server (new internal/reputation/
   package).
```

Until step 5, this document is a **design constraint** — the data we
need to capture during Phase 7.A is whatever ACR-200 will need to
analyse. That means `escrow_deposits` rows must include enough
context (agent_id, accepted_passage_count, etc.) to recompute weighted
acceptance retrospectively. **This is the only thing v0.1 enforces:
during Phase 7.A implementation, schema must preserve the data ACR-200
will need.**

---

## What this v0.1 is NOT

- **Not implementation-ready.** Two gates ahead.
- **Not a commitment to ARS as the metric.** R-1 might invalidate the
  whole formula.
- **Not a federation protocol.** Section 5 is a sketch; protocol-level
  federation is its own ACR (probably ACR-210).

---

ACR-200 Cross-Covenant Reputation v0.1-DRAFT · 2026-05-09 · gated on Phase 7.A real-tx data
