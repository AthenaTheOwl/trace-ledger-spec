# Tasks — Design batch

## PR 0005 — per-event-type payload schemas

- [ ] Author 11 payload schemas under `spec/payloads/`, one per
      event_type listed in `spec/event-types.yaml`.
- [ ] Extend `trace_ledger_spec/validator.py`:
      `load_payload_schemas()` plus payload-pass inside
      `validate_event` and `validate_ledger`.
- [ ] Extend `scripts/validate_schemas.py` to enforce
      one-payload-schema-per-event-type.
- [ ] Add `tests/test_payloads.py` covering: every example event
      satisfies its payload schema; a deliberately broken payload is
      reported with `payload:` prefix; a missing payload schema for
      a declared event_type fails the gate.
- [ ] Add `examples/bad_payload.jsonl` (a `tool.call.completed`
      event missing `result_ref`).
- [ ] Bump `spec/VERSION` to `0.2.0`; add a row to
      `spec/MIGRATIONS.md` describing the per-type payload addition
      as additive (minor bump).

## PR 0006 — append CLI

- [ ] Implement `trace_ledger_spec/appender.py` with
      `append_event(ledger_path, *, event_type, payload, actor,
      ledger_id=None, timestamp=None)` returning the written event
      dict.
- [ ] Add `append` subcommand to `trace_ledger_spec/cli.py`.
- [ ] Add `tests/test_appender.py`: round-trip (append then
      validate the resulting ledger), reject on bad payload, reject
      on unknown event_type, create-from-empty path, lockfile
      contention.
- [ ] Add `tests/test_cli_append.py`: argv parsing and
      `--payload @file` vs inline json.
- [ ] Refit `scripts/regen_examples.py` onto
      `appender.append_event` with pinned timestamps.
- [ ] Update `README.md` with an `append` example.

## PR 0007 — docs and gate hardening

- [ ] Land
      `decisions/DEC-TLS-003-payload-schemas-are-per-event-type.md`.
- [ ] Land `decisions/DEC-TLS-004-append-cli-uses-lockfile.md`.
- [ ] Extend `scripts/voice_lint.py` allowlist to cover the new
      payload-schema descriptions if needed.
- [ ] Tag `v0.2`.
