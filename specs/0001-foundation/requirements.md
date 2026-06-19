# Requirements — Foundation

Brand prefix: TLS (trace-ledger-spec).

## Schema requirements

- **R-TLS-001** — The repo SHALL publish `spec/trace-event.schema.json`
  describing the canonical event shape with required fields:
  `event_id`, `ledger_id`, `seq`, `timestamp`, `actor`, `event_type`,
  `payload`, `prev_hash`.
- **R-TLS-002** — `event_id` SHALL be a content-addressable hash of
  the event payload plus `prev_hash`, enabling tamper detection.
- **R-TLS-003** — `seq` SHALL be a monotonic per-ledger integer
  starting at 0. Gaps fail validation.
- **R-TLS-004** — `event_type` SHALL be drawn from a controlled
  vocabulary defined in `spec/event-types.yaml`, version-pinned.

## Append-only requirements

- **R-TLS-005** — The reference ledger SHALL reject any write that
  is not an append at the current `seq + 1`.
- **R-TLS-006** — The reference ledger SHALL reject any write whose
  `prev_hash` does not match the previous event's `event_id`.
- **R-TLS-007** — The reference ledger SHALL provide read-only
  iteration in `seq` order.

## Replay requirements

- **R-TLS-008** — The replay CLI SHALL accept a ledger plus a policy
  file plus an optional model-tools fingerprint, and produce a
  typed replay report indicating which decisions would have changed
  under the new policy.
- **R-TLS-009** — Replay SHALL be deterministic given the same
  ledger + policy + fingerprint inputs.

## Spec-governance requirements

- **R-TLS-010** — `spec/VERSION` SHALL follow semver. Breaking
  schema changes bump major; additive changes bump minor.
- **R-TLS-011** — Every spec change SHALL add a row to
  `spec/MIGRATIONS.md` describing the change, the version, and the
  migration path for existing ledgers.
- **R-TLS-012** — `spec/RFC-001-trace-event-format.md` SHALL exist
  and be normative (RFC-2119 keywords); the schema is the
  machine-readable shadow of the RFC.

## Voice and gate requirements

- **R-TLS-013** — The RFC and README SHALL pass voice_lint.
- **R-TLS-014** — All examples under `examples/` SHALL validate
  against the schema before merge.
