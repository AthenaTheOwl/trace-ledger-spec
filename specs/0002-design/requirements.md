# Requirements — Design batch

Brand prefix: TLS (trace-ledger-spec).

This batch follows the v0.1 schema-publishing work in
`specs/0001-foundation` and pins the next two concrete chunks: per-
event-type payload schemas, and an `append` CLI that computes chain
fields for the caller. Storage backends and replay land in later
batches.

## Per-type payload requirements

- **R-TLS-020** — Each name in `spec/event-types.yaml` SHALL have a
  matching payload schema under `spec/payloads/<name>.schema.json`.
  Missing payload schemas SHALL fail
  `scripts/validate_schemas.py`.
- **R-TLS-021** — `validate_event` SHALL apply the payload schema for
  the event's declared `event_type` and surface payload-schema
  errors with a `payload:` prefix.
- **R-TLS-022** — A payload schema SHALL declare
  `additionalProperties: false` unless a free-form extension surface
  is explicitly documented in the schema's `description`.
- **R-TLS-023** — Adding a new event_type SHALL be a minor version
  bump. Changing or removing an existing payload schema SHALL be a
  major version bump.

## Append-CLI requirements

- **R-TLS-030** — `python -m trace_ledger_spec append <ledger.jsonl>
  --type <name> --payload <json|@file> [--actor-type <t>] [--actor-id
  <id>]` SHALL append one event to `<ledger.jsonl>` with `seq`,
  `prev_hash`, `event_id`, and `timestamp` filled in by the CLI.
- **R-TLS-031** — `append` SHALL reject the call if the resulting
  event would fail `validate_event` (schema, vocab, or payload).
  Reject means: no write to disk, non-zero exit, error to stderr.
- **R-TLS-032** — `append` SHALL be safe to invoke concurrently on
  the same file from a single host. The reference implementation
  MAY use a lockfile next to the ledger (`<ledger>.lock`).
- **R-TLS-033** — If the ledger file does not exist, `append` SHALL
  create it and treat the new event as `seq = 0` with
  `prev_hash = sha256:` + 64 zeros.
- **R-TLS-034** — `append` SHALL be byte-deterministic given a fixed
  `--timestamp` override (used in tests and example regeneration).

## Voice and gate requirements

- **R-TLS-040** — Payload schemas SHALL pass voice_lint where they
  contain prose `description` fields.
- **R-TLS-041** — All example ledgers under `examples/` SHALL still
  validate after the per-type payload schemas land. Negative
  examples MAY be extended (e.g. `bad_payload.jsonl`) but
  `valid.jsonl` SHALL continue to pass unchanged.
