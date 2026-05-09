# ACR-510｜Multi-Rail Payment Routing
## x402 + Base L2 + Fiat + Multi-Hop · v0.1-DRAFT · May 2026

> ⚠️ **SPECULATIVE — gating remains.**
>
> Per `ACP_Roadmap.md` §Phase 7.B: this work is gated on Phase 7.A
> (Escrow + Auto-Settlement, ACR-500) landing first. Multi-rail payment
> without a working single-rail escrow is premature complexity.

---

## Provenance

| | |
|---|---|
| Status | DRAFT — awaiting Phase 7.A v0.3 ratification + initial implementation |
| Authors | working group |
| Last update | 2026-05-09 |
| Implementation gate | Phase 7.A live AND ≥10 successful escrow settlements on the v1 rail |
| Numbering | ACR-510 (extension of ACR-500 escrow) |

---

## What problem this solves

ACR-500 v0.2 specifies **single-asset, single-rail** escrow (decision
C-6). That's correct for the v1 implementation — multi-asset support
would slow down ratification by months. But once Phase 7.A is real and
proven, ACR-510 specifies how Covenants gain optionality:

- **x402 micropayments** for high-frequency low-value Agent-to-Agent
  flows (per-call settlement)
- **Base L2 ERC-20 settlement** for moderate-value periodic payouts
- **Fiat gateway** (ACH / Stripe) for participants who don't operate
  in crypto
- **Multi-hop routing** so Agent A can pay Agent B who pays Agent C in
  a chain, with each hop respecting its own Covenant's rules

ACR-500 is "money in, money out for one Covenant." ACR-510 is "money
in, money through one or more Covenants, paid out wherever participants
expect it."

---

## Core concepts

### Rail registry

A pluggable registry of payment rails:

```
type Rail interface {
    Name() string                                // "x402-base", "base-erc20", "stripe-ach", ...
    Class() RailClass                            // Micropayment | Periodic | Fiat
    Currencies() []string                        // supported asset codes
    Lock(deposit Deposit) (LockReceipt, error)   // for use in escrow
    Release(distribution Distribution) (ReleaseReceipt, error)
    Refund(refund Refund) (RefundReceipt, error)
    Estimate(amount AmountMinor, params ...Param) (FeeEstimate, error)
}
```

acp-server ships with a reference implementation of each rail class.
Operators may register custom rails via a config file at boot.

### x402 micropayment rail

Per the x402 spec, payment metadata is sent in HTTP headers alongside
the API call. ACP's adaptation:

```
Agent A calls Agent B's tool:
  POST /tools/transcribe
  X-402-Payment: <signed-payment-token>
  X-402-Amount-Minor: 50    (USDC cents = $0.50)
  X-402-Covenant-Id: <CID>

Agent B's acp-server:
  1. Validate X-402-Payment signature (Agent A's session-bound key)
  2. Lock 50 minor units from Agent A's escrow balance for the Covenant
  3. Execute the tool
  4. On success: release 50 to Agent B
  5. On failure: refund 50 to Agent A (atomically, no double-spend)
```

x402 is a **per-call** rail. Settlement happens before the response
returns. Useful for Agent ecosystems where every API call has a
microcost.

### Base L2 ERC-20 rail

Direct integration with Base mainnet (or Sepolia testnet). At Covenant
settlement:

```
1. acp-server reads escrow_releases.distributions
2. For each (claimant_wallet, amount_minor, gas_minor):
     server submits an ERC-20 transfer (USDC, by default)
     using the custody adapter (ACR-500 §9 Profile A or B)
3. Each transfer's tx_hash is written back to the audit log
4. claimant_wallet receives the tokens directly — no Pull required
```

The ERC-20 push is **opt-in per Covenant**. Claimants who prefer
ACR-100 §4 Pull-style withdrawal can stay on that rail; the choice is
per-claimant at member-add time.

### Fiat gateway rail

Adapter pattern with implementations for:

- **Stripe** — ACH transfers + cards out, requires Stripe Connect setup
- **Wise** — international payouts, lower friction for cross-border
- **Bank ACH** — direct bank file generation (NACHA format), for
  operators with banking integrations

Fiat rails are **complianced** — the operator is on the hook for KYC
above ACR-50's $1,000 threshold (already specified). ACR-510 does not
re-specify KYC.

### Multi-hop payment routing

The ambitious one. Pattern:

```
User → wants Agent A to deliver outcome X
     → Agent A subcontracts Agent B for sub-task Y
     → Agent B subcontracts Agent C for sub-sub-task Z

Each hop is its own Covenant.

When user settles to A: $1000
A's Covenant settles internally according to its rules (e.g.,
  90% to A, 10% to A's vendor pool)
A's vendor pool flows into B's Covenant: $100
B's Covenant settles: 80% B, 20% to C's pool
C's Covenant settles: $20 to C
```

ACR-510 specifies the **inter-Covenant transfer protocol**: how A's
escrow_pool releases funds INTO B's escrow_lock atomically. Without
atomicity, the chain is at risk of a hop succeeding while another
fails.

Implementation: each inter-Covenant transfer is itself a Covenant
member operation, with `receiving_covenant_id` instead of
`claimant_wallet`. The ACP server handles routing as long as both
Covenants live on it; cross-server multi-hop is an extension.

---

## Schema additions (informative)

```sql
-- Rail registration
CREATE TABLE rails (
    rail_id     TEXT PRIMARY KEY,                   -- 'x402-base', 'base-erc20-usdc', etc.
    class       TEXT NOT NULL CHECK(class IN ('micropayment','periodic','fiat')),
    config      TEXT NOT NULL,                       -- JSON, rail-specific
    enabled     BOOLEAN NOT NULL DEFAULT 1,
    registered_at DATETIME NOT NULL
);

-- Per-Covenant rail selection
ALTER TABLE covenants ADD COLUMN settlement_rail TEXT REFERENCES rails(rail_id);

-- Per-claimant rail override
ALTER TABLE covenant_members ADD COLUMN preferred_rail TEXT REFERENCES rails(rail_id);

-- Multi-hop linkage
CREATE TABLE inter_covenant_flows (
    flow_id         TEXT PRIMARY KEY,
    source_covenant TEXT NOT NULL REFERENCES covenants(id),
    target_covenant TEXT NOT NULL REFERENCES covenants(id),
    amount_minor    INTEGER NOT NULL,
    asset           TEXT NOT NULL,
    state           TEXT NOT NULL CHECK(state IN ('PENDING','COMMITTED','SETTLED','REFUNDED')),
    audit_hash_pin  TEXT NOT NULL,
    created_at      DATETIME NOT NULL
);
```

---

## Tool surface additions (PROVISIONAL)

| Tool | Purpose | Auth |
|---|---|---|
| `register_rail` | Operator registers a payment rail | Operator (boot config or admin) |
| `set_covenant_rail` | Owner picks the rail for a Covenant | Owner |
| `set_member_rail` | Member picks their preferred outbound rail | Member |
| `route_to_covenant` | Source Covenant sends funds to a target Covenant escrow | Owner of source |
| `get_rail_estimate` | Quote fees + ETA for a rail+amount | Member / Owner |

---

## Open questions

| # | Question | Why |
|---|---|---|
| MR-1 | Are micropayment + periodic rails mutually exclusive per Covenant? | Could a Covenant have x402 for live API calls AND periodic ERC-20 for settlement? Yes seems intuitive but creates accounting complexity |
| MR-2 | What's the failure mode if a rail goes down mid-settlement? | E.g., Base RPC outage during a multi-claimant release |
| MR-3 | Atomicity guarantee in multi-hop: 2PC, sagas, or eventual consistency? | Each has different operational profile |
| MR-4 | Cross-server multi-hop — is this in scope of ACR-510 or its own ACR? | Probably its own; ACR-510 is single-server |
| MR-5 | Does ACP track the relationship between hops in a chain (parent flows)? | Useful for UX but requires graph schema |
| MR-6 | Fee-pass-through semantics: when A settles $1000 to B, does B see $1000 minus rail fee or $1000? | Affects how the multi-hop tax stacks |
| MR-7 | Should fiat rails be allowed in cross-server flows? | Compliance landmine — different operators in different jurisdictions |

---

## Path to ratification

```
1. Phase 7.A v0.3 ratifies, ACR-500 v1 ships in acp-server.
2. ≥10 settlements complete on the v1 rail (Profile B multisig on Base).
3. Working group surveys actual usage patterns:
   - Are participants asking for x402 micropayments? Frequency-of-call?
   - Are participants asking for fiat?
   - Multi-hop demand?
4. ACR-510 v0.2 written against observed demand, not speculation.
5. Reference implementations of in-demand rails added to acp-server.
```

The order matters. Implementing all four rails before knowing which
is needed produces an over-engineered surface.

---

## What this v0.1 is NOT

- **Not implementation-ready.** Phase 7.A must ship and run for weeks
  first.
- **Not a commitment to all four rails.** Operators may need only one.
- **Not a multi-server federation protocol.** Cross-server flows are
  flagged as out-of-scope (MR-4).

---

ACR-510 Multi-Rail Payment Routing v0.1-DRAFT · 2026-05-09 · gated on Phase 7.A live + ≥10 settlements
