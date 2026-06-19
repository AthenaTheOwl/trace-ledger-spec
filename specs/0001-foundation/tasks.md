# Tasks — Foundation

## PR 0002 — schema, RFC, event-type vocabulary

- [ ] Write `spec/trace-event.schema.json` matching R-TLS-001
      through R-TLS-004.
- [ ] Write `spec/RFC-001-trace-event-format.md` (RFC-2119 prose).
- [ ] Author `spec/event-types.yaml` with the v0 controlled
      vocabulary.
- [ ] Initialize `spec/VERSION` at `0.1.0`.
- [ ] Initialize `spec/MIGRATIONS.md` with a single row.
- [ ] Add `scripts/voice_lint.py` (copy template).
- [ ] Add `scripts/validate_schemas.py` and
      `scripts/validate_examples.py` and
      `scripts/check_migration_log.py`.
- [ ] Add `pyproject.toml`.

## PR 0003 — SQLite reference ledger

- [ ] Implement `src/trace_ledger/ledger.py` (init, append,
      iterate).
- [ ] Implement `src/trace_ledger/hashing.py` for event_id +
      prev_hash chain.
- [ ] Add CLI `python -m trace_ledger {init,append,verify}`.
- [ ] Write `tests/test_append_only.py` covering gap rejection,
      bad-prev-hash rejection, monotonic seq.
- [ ] Write `tests/test_chain_verify.py` (tamper detection).
- [ ] Author `examples/minimal/` with 5 hand-crafted events.

## PR 0004 — replay CLI + worked example

- [ ] Implement `src/trace_ledger/replay.py`.
- [ ] Define `schemas/replay_report.schema.json`.
- [ ] Author `examples/procurement-negotiation-lab/` ledger and
      a sample policy file.
- [ ] Write `tests/test_replay_determinism.py`.
- [ ] Land `decisions/DEC-TLS-001-content-addressable-event-id.md`.
- [ ] Land `decisions/DEC-TLS-002-sqlite-as-v0-reference.md`.
- [ ] Tag `v0.1`.
