# DEC-TLS-001: sha256 content-addressed event ids

id: DEC-TLS-001
date: 2026-07-05
status: accepted

## decision

v0.1 event ids use content addressing. `event_id` is `"sha256:" + hexdigest` over canonical event bytes, where the canonical bytes are json with sorted keys, no whitespace, utf-8 encoding, and `event_id` excluded from the hash input. the genesis `prev_hash` value is `"sha256:" + ("0" * 64)`. this records the shipped R-TLS-002 mechanism from the 0001 foundation spec.

## alternatives considered

- opaque uuids: rejected because they identify records but do not make event content tamper-evident.
- hashing the serialized event including `event_id`: rejected because the field would make the hash self-referential and impossible to compute without a placeholder rule.

## rationale

content addressing makes a ledger event carry its own integrity check. excluding `event_id` keeps the hash computation deterministic, and the canonical json form gives independent implementations a byte-level target for conformance.

## evidence

- `specs/0001-foundation/requirements.md:11-12` defines R-TLS-002, requiring `event_id` to be a content-addressable hash of the event payload plus `prev_hash`.
- `trace_ledger_spec/validator.py:41` defines the genesis previous hash as a sha256 prefix plus 64 zeroes.
- `trace_ledger_spec/validator.py:64-70` defines canonical bytes as sorted-key json with no whitespace, utf-8 encoding, excluding `event_id`.
- `trace_ledger_spec/validator.py:73-75` computes `event_id` as a sha256 hex digest with the `sha256:` prefix.

## rollback

rollback would be a spec change. it would need a new version, migration note, and compatibility story for existing v0.1 ledgers whose ids are already derived from these canonical bytes.
