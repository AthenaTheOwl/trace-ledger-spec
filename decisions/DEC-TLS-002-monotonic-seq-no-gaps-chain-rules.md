# DEC-TLS-002: monotonic seq no-gaps chain rules

id: DEC-TLS-002
date: 2026-07-05
status: accepted

## decision

v0.1 ledgers use a strict per-ledger sequence chain. `seq` starts at 0 and increases by 1 for each event, gaps fail validation, and each event's `prev_hash` must equal the previous event's `event_id`. this records the shipped R-TLS-003, R-TLS-005, and R-TLS-006 mechanisms from the 0001 foundation spec.

## alternatives considered

- sparse sequence numbers: rejected because validators would need extra policy to distinguish intentional reservation from missing events.
- timestamp ordering: rejected because timestamps can collide, drift, or arrive out of order, while `seq` gives one deterministic append order.
- accepting a missing or arbitrary `prev_hash`: rejected because deletion or replacement of prior events would no longer be detected by chain validation.

## rationale

the ledger is append-only batch data, so validation needs a simple local rule for completeness and order. a no-gaps `seq` check catches missing entries, and the `prev_hash` link binds each event to the exact event before it.

## evidence

- `specs/0001-foundation/requirements.md:13-14` defines R-TLS-003, requiring `seq` to be monotonic per ledger, start at 0, and fail validation on gaps.
- `specs/0001-foundation/requirements.md:20-23` defines R-TLS-005 and R-TLS-006, requiring append at current `seq + 1` and matching `prev_hash`.
- `trace_ledger_spec/validator.py:151-154` reports a `seq` gap when the event sequence does not match the expected value.
- `trace_ledger_spec/validator.py:156-160` reports a `prev_hash` mismatch when the event does not point to the previous event id.

## rollback

rollback would require a new spec version, migration note, and validator mode for older ledgers. existing v0.1 ledgers assume no-gaps sequence order and previous-event hash chaining.
