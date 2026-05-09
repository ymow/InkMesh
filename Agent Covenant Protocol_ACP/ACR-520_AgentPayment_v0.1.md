# ACR-520｜Agent Autonomous Payment Mandate
## Pre-authorized self-directed payments by AI agents · v0.1-DRAFT · May 2026

> ⚠️ **SPECULATIVE — gating remains.**
>
> Per `ACP_Roadmap.md` §Phase 7.C: this work is gated on Phase 7.B
> (multi-rail payment, ACR-510) shipping enough rails for autonomous
> payments to be useful. ACR-520 also requires real Agent ecosystems
> where this autonomy provides measurable utility — building it
> against speculation invites exploits.

---

## Provenance

| | |
|---|---|
| Status | DRAFT — awaiting Phase 7.B + observed Agent autonomy demand |
| Authors | working group |
| Last update | 2026-05-09 |
| Implementation gate | Phase 7.B operational + ≥3 distinct Agent ecosystems requesting autonomous payment |
| Numbering | ACR-520 (Phase 7.C extension of escrow standard) |

---

## What problem this solves

Today, every payment in ACP requires explicit Owner approval (via
`approve_draft`, `confirm_settlement_output`, etc.). For Agent-to-
Agent micro-economies, this is a bottleneck — an Agent that needs to
call a paid tool 100 times an hour can't wait for human approval each
time.

ACR-520 specifies how an Owner can **pre-authorize** an Agent to
make payments autonomously, within constrained parameters:

- **Spending caps** (per-tx, per-hour, per-day, total)
- **Whitelist of recipients** (specific Agents, Covenants, or rails)
- **Time windows** (only during X hours, only until date Y)
- **Purpose constraints** (only for tools matching pattern Z)
- **Revocation** (Owner can yank the mandate at any time, retroactive)

The Owner trades convenience-of-no-approval for risk-of-misuse,
explicitly and bounded.

---

## Core concepts

### Payment Mandate

A signed authorization with structured constraints:

```json
{
  "mandate_id": "mnd_abc123",
  "covenant_id": "cvnt_xyz",
  "agent_id": "agent_alice",
  "issued_by": "owner_token_signer",
  "issued_at": "2026-05-09T00:00:00Z",
  "constraints": {
    "max_per_tx": 1000,                    // $0.01 USDC if minor units = USDC cents
    "max_per_hour": 10000,                 // $1.00/hour
    "max_per_day": 100000,                 // $10/day
    "max_total": 1000000,                  // $100 lifetime
    "spent_so_far_minor": 0,
    "recipient_whitelist": [
      "agent:agent_bob",
      "covenant:cvnt_data_processor",
      "rail:x402-base"
    ],
    "purpose_pattern": "tools/transcribe/*",
    "valid_from": "2026-05-09T00:00:00Z",
    "valid_until": "2026-08-09T00:00:00Z",
    "valid_hours_utc": [9, 10, 11, 12, 13, 14, 15, 16, 17]
  },
  "audit_hash_pin": "0xabcd...",
  "revoked_at": null,
  "revoked_by": null
}
```

The mandate is signed (using ACR-700 keyring). Revocation is recorded
with `revoked_at`/`revoked_by` — once revoked, it's permanently dead;
no re-activation.

### Spending budget per Agent

Each `(covenant_id, agent_id)` pair has a tracked budget:

```sql
CREATE TABLE agent_spending_budgets (
    covenant_id     TEXT NOT NULL,
    agent_id        TEXT NOT NULL,
    mandate_id      TEXT NOT NULL,
    spent_minor     INTEGER NOT NULL DEFAULT 0,
    spent_this_hour INTEGER NOT NULL DEFAULT 0,    -- reset hourly
    spent_today     INTEGER NOT NULL DEFAULT 0,    -- reset daily UTC
    last_reset_at   DATETIME NOT NULL,
    PRIMARY KEY (covenant_id, agent_id, mandate_id)
);
```

Budgets are scoped per-mandate. An Agent could have multiple active
mandates (e.g., one for tool calls, one for vendor payments) — each is
independent.

### Payment Audit Trail

Every autonomous payment writes an ACR-300 audit-log entry:

```
action:    "autonomous_payment"
actor:     <agent_id>
mandate:   <mandate_id>
recipient: <recipient_id>
amount_minor: <amount>
currency:  <asset>
purpose:   <tool_or_covenant_action>
audit_hash_prev: <previous chain hash>
audit_hash:      <new chain hash>
```

The mandate_id binds the payment to its authorization. Auditors can
trace any payment back to:
1. Which mandate authorized it
2. Who issued the mandate
3. What constraints existed at the time
4. Whether the constraints were satisfied at execution

### Revocation

Owner can revoke at any time:

```
POST /tools/revoke_mandate
Body: { "params": { "mandate_id": "mnd_abc123", "reason": "agent compromised" } }
Auth: X-Owner-Token
```

Effects:
- All future payment attempts referencing this mandate fail with
  `ErrMandateRevoked`.
- In-flight payments (rare but possible mid-tx) complete; future
  re-authorization-required calls fail.
- Audit log gets a `mandate_revoked` entry.

Refund of already-spent amounts is **not** automatic. If the Owner
believes an Agent abused the mandate before revocation, the dispute
goes through Phase 7.D's resolution (or off-ACP legal channels).

---

## Tool surface

| Tool | Purpose | Auth |
|---|---|---|
| `issue_mandate` | Owner issues a payment mandate to an Agent | Owner |
| `revoke_mandate` | Owner revokes; takes effect immediately | Owner |
| `list_mandates` | Owner lists all mandates for a Covenant | Owner |
| `get_mandate_status` | Agent queries their own active mandate(s) | Agent |
| `autonomous_payment` | Agent invokes a payment under a mandate | Agent (with mandate_id) |

---

## Constraint evaluation order

When `autonomous_payment` is called, the server evaluates in order:

```
1. Mandate exists AND is_revoked == false
2. Now is within [valid_from, valid_until]
3. Now is within valid_hours_utc (if set)
4. Recipient matches recipient_whitelist (any rule)
5. Purpose matches purpose_pattern (glob)
6. Asset matches mandate's currency
7. amount_minor <= max_per_tx
8. (spent_this_hour + amount_minor) <= max_per_hour
9. (spent_today + amount_minor) <= max_per_day
10. (spent_so_far_minor + amount_minor) <= max_total
11. Atomically: increment all counters, write audit log, route payment
```

If any check fails, the call returns a structured error indicating
WHICH check failed (for the Agent's UI to surface intelligibly).

---

## Open questions

| # | Question | Why |
|---|---|---|
| AP-1 | Should mandates support whitelisting tool patterns by glob, regex, or only exact string? | Glob is simpler; regex more powerful but harder to audit |
| AP-2 | What's the recovery for an Agent that loses its session token mid-mandate? | Mandate is bound to agent_id, not session — re-issuing session shouldn't break |
| AP-3 | Can mandates compound (one Agent issues a sub-mandate to another)? | "Sub-mandates" are conceptually similar to Phase 7.B multi-hop. Defer to ACR-510. |
| AP-4 | Audit trail: should mandates record their constraints in the chain so future verifiers can confirm spending was in-bounds? | Yes likely; specifics TBD |
| AP-5 | Should there be a global "panic button" that revokes all mandates for a Covenant? | Useful in compromise scenarios; simple to implement |
| AP-6 | Multi-Owner Covenants: do mandates require unanimous consent or quorum? | Unrelated to mandates per se; depends on multi-Owner schema (not yet specified) |

---

## Anti-patterns

These are explicitly disallowed in ACR-520 v0.1:

1. **Open-ended mandates.** Mandate MUST have a `valid_until` ≤
   `valid_from + 1 year`. Forever-mandates are forbidden.
2. **Wildcard recipients.** `recipient_whitelist: ["*"]` is rejected.
   Authorization without scope is not authorization.
3. **Self-mandate.** An Agent cannot be in both `issued_by` and
   `agent_id` (would let Agents sign their own permissions).
4. **Mandate transferability.** Mandates are bound to a specific
   `agent_id`; re-issuing to a different agent requires a fresh
   mandate, not a transfer.

---

## What this v0.1 is NOT

- **Not implementation-ready.** Phase 7.B must ship first.
- **Not a general "Agent has bank account" abstraction.** Mandate is
  scoped to Covenant; Agents don't accumulate independent balances.
- **Not a substitute for Owner approval where it matters.** Mandates
  enable convenience for low-stakes flows; high-stakes payments still
  require explicit `approve_draft`.

---

ACR-520 Agent Autonomous Payment Mandate v0.1-DRAFT · 2026-05-09 · gated on Phase 7.B
