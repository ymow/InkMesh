# ACR-500｜Covenant Escrow Standard
## Funded Covenant & Settlement Execution · v0.2-PROVISIONAL · May 2026

> ⚠️ **PROVISIONAL — DO NOT IMPLEMENT.**
>
> v0.2 promotes every v0.1 default through a **PROVISIONAL** stamp. The
> ten decisions in `ACR-500_Decisions_v0.1.md` remain OPEN. Operators
> reading this should treat each PROVISIONAL block as **not yet
> ratified by the working group**. Implementation MUST NOT begin from
> v0.2 alone — v0.3 (with explicit RATIFIED markers) is the
> implementation gate.
>
> The point of v0.2 is to make the assumed-defaults visible as a single
> coherent draft so working-group members can review the *aggregate
> picture* before voting on individual decisions. v0.1 + v0.1-Decisions
> separately produces ten conditional branches; v0.2 collapses them
> into one walkable spec.

---

## Provenance

| | |
|---|---|
| Supersedes | ACR-500_Escrow_v0.1 + ACR-500_Decisions_v0.1 (this draft consolidates both) |
| Status | PROVISIONAL — pending ratification of C-1..C-10 |
| Authors | working group |
| Last update | 2026-05-09 |
| Implementation gate | v0.3 (post-ratification) |

---

## What changed v0.1 → v0.2

```
For each of C-1..C-10, the v0.1 default is promoted into the body of
the spec, with the source decision row inlined as a [PROVISIONAL: C-N]
sidebar. No semantic invention beyond v0.1 defaults — only consolidation
and call-out.
```

| Decision | v0.1 default → v0.2 PROVISIONAL stamp | Reversal cost (if working group says no) |
|---|---|---|
| C-1 Spec authority | ACR-500 supersedes REVIEW-07; ACR-100 §4 preserved as withdrawal rail | ACR-100 §4 rewrite + REVIEW-07 reopen |
| C-2 Escrow ⇄ x402 layering | Stacked: escrow source, x402 rail | New `pull-only` rail + `escrow_id NULL` path |
| C-3 Lock timing | DRAFT → OPEN transition | Re-time to ACTIVE; UX impact |
| C-4 Budget growth | Top-up required (`ErrEscrowTopUpRequired`) | Allow over-allocation; circuit-breaker on acceptance overflow |
| C-5 reject_draft escrow refund | No — escrow no-op on reject_draft | New refund accounting + audit type |
| C-6 Single-asset escrow | Single asset only | Multi-asset state + exchange-rate snapshots |
| C-7 Custody | Profile B (multisig) testnet first; Profile A audit before mainnet | Custody adapter completely different |
| C-8 Gas allocation | Deduct from claimant share | Settlement math + payout previews change |
| C-9 Settlement timeout | 180 days | Different post-timeout state |
| C-10 Departed agent claims | Yes (Constitutional §5) | leave_covenant gains `unclaimed_at` |

---

## Body — promoted defaults inline

(The following sections mirror v0.1 of `ACR-500_Escrow_v0.1.md` with
PROVISIONAL stamps where v0.1 deferred to a decision. Sections without
stamps are inherited verbatim from v0.1 and unchanged.)

### Part 2｜Relationship to ACR-100 v0.3

> **PROVISIONAL: C-1, C-2.** ACR-500 sits **above** ACR-100 §4. ACR-100
> §4 (x402 Pull withdrawal flow) is **preserved** as the rail used for
> Owner → Claimant fund movement. ACR-500 §6 is the *source of funds*;
> ACR-100 §4 is the *transport*.
>
> Working group must ratify C-1 to lock in this layering and C-2 to
> confirm there is no `pull-only` escape hatch for unbacked withdrawals.

### Part 5｜Lock Semantics

#### 5.1 When the lock takes effect

> **PROVISIONAL: C-3.** Lock takes effect at the **DRAFT → OPEN**
> transition. Owner deposits funds (or commits the deposit reference)
> before the Covenant becomes joinable. Race conditions where a
> contributor proposes before the deposit lands are rejected with
> `ErrEscrowNotLocked`.
>
> Reversal: would re-time to ACTIVE (first contribution boundary), at
> the cost of contributor-side waiting and a more complex state graph.

#### 5.2 Budget growth after lock

> **PROVISIONAL: C-4.** After lock, owner may attempt to grow the
> Covenant budget via `set_budget`. If `escrow.locked_amount <
> new_budget`, the call returns `ErrEscrowTopUpRequired` and instructs
> the owner to deposit the delta first. The error includes
> `required_top_up_minor` so the UI can render a one-click top-up.

### Part 6｜Release Semantics

#### 6.1 Trigger

Inherited from v0.1 — settlement confirmation triggers release. No
PROVISIONAL stamp; the question is *what releases*, not *when*.

#### 6.5 Reject draft semantics

> **PROVISIONAL: C-5.** `reject_draft` releases the reserved budget
> back to the available-budget pool but does **not** emit any
> `escrow.*` audit event. Escrow ledger moves only on
> deposit / release / refund / top-up. Reject-cycles internal to a
> Covenant are bookkeeping in the budget gate, not in escrow.

### Part 7｜Failure Modes & Default Positions

#### 7.6 Asset boundary

> **PROVISIONAL: C-6.** One Covenant carries **one asset** (one
> Account, one Rail). Multi-asset escrow is a v0.3+ extension; the
> v0.2 schema does not include `escrow_assets` child rows.
>
> If a Covenant needs multi-asset, the workaround is a parent owner
> tracking multiple Covenants (one per asset) with bookkeeping
> external to ACP.

### Part 9｜Custody Model

> **PROVISIONAL: C-7.** Reference v1 implementation:
>
> - **Testnet pilot:** Profile B — 2-of-2 multisig (Owner key + server
>   hot key). Base Sepolia. Lower audit cost, acceptable for pilot
>   transactions ≤ $10,000 USDC equivalent.
> - **Mainnet:** Profile A — audited Solidity escrow contract on Base
>   mainnet. Audit critical path: 6–8 weeks, contracted to a reputable
>   auditor (working group selects). Until audit completes, mainnet
>   stays on Profile B with a per-Covenant cap.
>
> Profile C (WaaS / Magic / Privy) is explicitly NOT the v1 reference;
> vendor lock is a regression on the protocol's "anyone can run their
> own server" stance.

### Part 10｜Gas / Fee Allocation

> **PROVISIONAL: C-8.** The on-chain gas (or fiat rail fee) on
> withdrawal is **deducted from the claimant's share**. `amount_minor`
> in `Distribution` is the **net** the claimant receives.
>
> `get_token_balance` displays both `gross` and `net` (with
> `gas_estimate_minor`) so claimants understand the deduction before
> initiating withdrawal. Gas estimates are quoted with a 20% buffer;
> any unspent gas is forwarded to the claimant in a follow-up tx
> (or absorbed into the escrow residue at settlement, working group
> chooses at C-8 ratification).

### Part 11｜Settlement Timeout

> **PROVISIONAL: C-9.** A Covenant in ACTIVE state with no
> `propose_passage` activity for **180 days** becomes eligible for
> emergency settlement. Per-Covenant override allowed via
> `configure_token_rules.settlement_timeout_days` within bounds
> `[30, 730]`.
>
> A background watchdog scans `covenants.last_passage_at` once daily;
> exceeded Covenants emit a notification (audit-log + webhook if
> configured) but do NOT auto-settle. Owner action remains required —
> the timeout shifts the burden, doesn't remove it.

### Part 12｜Departed Agent Claim Rights

> **PROVISIONAL: C-10.** An agent who invokes `leave_covenant` retains
> claim rights to any tokens earned before departure. At settlement,
> their share is included in the withdrawal offer set. This aligns
> Constitutional Principle 5 (退出權): leaving a Covenant doesn't
> erase work already accepted.
>
> Implementation: `leave_covenant.go` MUST NOT delete `token_ledger`
> rows (already true in v0.4.6). `withdrawal_offers` issuance includes
> agents whose `covenant_members.status = 'left'` if their token total
> > 0. `list_members` returns a `left` enum value distinct from
> `active` and `pending`.

---

## Schema additions (informative, NOT FROZEN)

> ⚠️ Even after C-1..C-10 ratification, the schema below requires its
> own review — naming, types, and indexes are PROVISIONAL.

```sql
CREATE TABLE covenant_escrows (
    covenant_id     TEXT PRIMARY KEY REFERENCES covenants(id),
    asset           TEXT NOT NULL,                      -- e.g. 'USDC-base-sepolia'
    custody_profile TEXT NOT NULL CHECK(custody_profile IN ('A','B','C')),
    locked_minor    INTEGER NOT NULL DEFAULT 0,         -- net of releases + refunds
    state           TEXT NOT NULL CHECK(state IN ('PENDING','LOCKED','RELEASED','REFUNDED','EXPIRED')),
    custody_ref     TEXT,                                -- contract address or multisig id
    created_at      DATETIME NOT NULL DEFAULT (datetime('now')),
    locked_at       DATETIME,
    released_at     DATETIME,
    refunded_at     DATETIME
);

CREATE TABLE escrow_deposits (
    deposit_id      TEXT PRIMARY KEY,
    covenant_id     TEXT NOT NULL REFERENCES covenant_escrows(covenant_id),
    amount_minor    INTEGER NOT NULL,
    rail_tx_hash    TEXT NOT NULL,                       -- on-chain or rail-specific
    created_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE escrow_releases (
    release_id      TEXT PRIMARY KEY,
    covenant_id     TEXT NOT NULL REFERENCES covenant_escrows(covenant_id),
    settlement_id   TEXT NOT NULL,                       -- ACR-100 settlement reference
    distributions   TEXT NOT NULL,                       -- JSON: [{agent_id, amount_minor, gas_minor}, ...]
    rail_tx_hash    TEXT NOT NULL,
    created_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);
```

`covenant_members` gains:
```sql
ALTER TABLE covenant_members ADD COLUMN claimant_wallet TEXT;
ALTER TABLE covenant_members ADD COLUMN gas_responsibility TEXT
    DEFAULT 'claimant'
    CHECK(gas_responsibility IN ('claimant','owner','escrow_pool'));
```

(`gas_responsibility` defaults to `claimant` per C-8 v0.1 default; owner
override at member-add time supports unusual cases where, e.g., a
sponsor pre-pays gas for a specific agent.)

---

## Tool surface additions (PROVISIONAL)

| Tool | Purpose | Auth |
|---|---|---|
| `lock_escrow` | Owner locks a deposit reference into the Covenant escrow at DRAFT → OPEN | Owner |
| `top_up_escrow` | Owner adds to existing locked amount | Owner |
| `release_to_claimants` | Auto-called on `confirm_settlement_output`; idempotent | System |
| `refund_to_owner` | Emergency settlement / Owner abandonment path | Owner + 2nd factor |
| `get_escrow_status` | Read current lock_state, balance, custody_ref | Owner / Member |

All five tools emit ACR-300 audit-log entries with new action types
`escrow.lock`, `escrow.top_up`, `escrow.release`, `escrow.refund`. Hash
chain payloads include `escrow_tx_hash` for off-chain verifiability.

---

## What this v0.2 is NOT

- **Not implementation-ready.** v0.3 (post-ratification) is the gate.
- **Not a fork of v0.1.** Treat v0.1 + v0.1-Decisions as the true
  source; v0.2 is the *consolidated review surface* for working group.
- **Not a commitment to defaults.** Every PROVISIONAL stamp is a yes/no
  question. Working group can flip any of them at C-N ratification and
  v0.3 will reflect.

---

## Path to v0.3

```
1. Working group reviews v0.2 (this doc).
2. Per-decision votes in PHASE-7A-DECISIONS.md.
3. Decisions log appended in v0.1-Decisions.md.
4. v0.3 author takes resolved decisions, removes PROVISIONAL stamps
   for accepted ones, rewrites sections for rejected-with-resolution
   ones.
5. v0.3 is RATIFIED. Implementation begins.
```

Until v0.3 lands, **no escrow code merges into acp-server main**, even
behind feature flags. Speculative implementation against PROVISIONAL
v0.2 is the anti-pattern this whole structure exists to prevent.

---

ACR-500 Escrow v0.2-PROVISIONAL · 2026-05-09 · pending C-1..C-10 ratification
