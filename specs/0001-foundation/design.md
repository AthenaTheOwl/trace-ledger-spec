# Design — Foundation

## Shape

Spec on top, reference implementation underneath, conformance suite
to one side.

```
        spec/RFC-001-trace-event-format.md   (normative prose)
        spec/trace-event.schema.json         (machine shape)
        spec/event-types.yaml                (controlled vocab)
        spec/VERSION + spec/MIGRATIONS.md    (version discipline)
                       |
            +----------+----------+
            |                     |
   reference impl          conformance suite
   (SQLite append-only)    (v1; not in v0)
            |
       replay CLI
            |
       eval CLI (calls into trace-to-eval-harness primitives)
```

## Why the spec is the load-bearing artifact

A standard wins if it ships first and proves implementable. Two
implementations + a conformance suite turns "my repo's design" into
"a spec." The point of v0 is to nail the schema and the
append-only invariants so v1 can add a second implementation (likely
Postgres-backed) and bless the conformance suite.

## Event shape

```json
{
  "event_id": "sha256:c4ab...3f9e",
  "ledger_id": "01HX7B3J5K2",
  "seq": 17,
  "timestamp": "2026-06-19T14:23:11.402Z",
  "actor": {
    "type": "agent",
    "id": "supplier-risk-rag-agent@v0.4.2",
    "session": "01HX7B3J5K2-session-3"
  },
  "event_type": "tool.call.completed",
  "payload": {
    "tool": "search_filings",
    "args": {"query": "Anthropic 8-K capacity Q2"},
    "result_ref": "blob://sha256:7d2e...91ab",
    "latency_ms": 412
  },
  "prev_hash": "sha256:8f1c...22ad"
}
```

## Why content-addressable event_id

Tamper-evidence comes from the prev_hash chain. If any past event
is altered, every downstream `event_id` changes and the chain
breaks at the altered point. This is the same primitive Notary
Layer uses for receipts; the two specs deliberately share their
hash discipline.

## Append-only enforcement

The SQLite reference uses a single table `events` with a UNIQUE
constraint on `(ledger_id, seq)` and a CHECK trigger that the new
event's `prev_hash` equals the previous event's `event_id`.
Application code wraps each append in a transaction. No update
statements exist in the reference implementation.

## Replay semantics

Replay takes a ledger plus a *new* policy file and walks events in
seq order. For each `policy.decision.evaluated` event in the
original ledger, replay re-runs the decision under the new policy
and records the delta. Output is a typed replay report listing
(seq, original_decision, replayed_decision, changed).

Determinism requires the model-tools fingerprint match. Replay
against a different fingerprint produces a "non-comparable" report
with explicit reason.

## Worked example

`examples/procurement-negotiation-lab/` contains a real ledger from
a procurement-negotiation-lab session: 230-ish events covering one
RFx round. The example doubles as the conformance-suite seed.

## Dependencies

- `sqlite3` (stdlib).
- `pydantic` for typed events.
- `jsonschema` for spec validation.
- `pyyaml` for event-types vocabulary.

No web framework. No ORM. The reference implementation is
deliberately small.

## What is deliberately NOT in v0

- A second backend (Postgres / S3).
- Multi-tenant access control.
- Real-time streaming append APIs (the v0 append is sync, batch-
  oriented).
- Cross-ledger query / joins.
- A web UI.
