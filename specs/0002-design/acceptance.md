# Acceptance — Design batch

"design batch done" means every event_type has a payload schema, the
validator enforces it, and an `append` CLI produces ledgers that the
validator accepts without any caller knowing the canonical-bytes
recipe.

## Commands a reviewer must be able to run

```bash
python -m pip install -e . --group dev

# the existing default still works.
python -m trace_ledger_spec validate

# new: append against an empty ledger.
python -m trace_ledger_spec append /tmp/demo.jsonl \
    --ledger-id 01HX-DEMO \
    --type session.start \
    --actor-type agent --actor-id demo-agent@v0 \
    --payload '{"session_id": "01HX-DEMO-1"}'

python -m trace_ledger_spec append /tmp/demo.jsonl \
    --type tool.call.completed \
    --actor-type agent --actor-id demo-agent@v0 \
    --payload @examples/payloads/tool_call_completed.json

# round-trip: the just-written ledger validates clean.
python -m trace_ledger_spec validate /tmp/demo.jsonl
```

## Gates that must pass

- `python -m pytest` exits 0 with the new test files included.
- `python scripts/validate_schemas.py spec/` exits 0 and confirms
  one payload schema per declared event_type.
- `python scripts/validate_examples.py examples/` exits 0; negative
  examples still report `expect_fail` correctly.
- `python scripts/voice_lint.py spec/ docs/ README.md` exits 0
  against the new payload-schema descriptions.
- `python scripts/check_migration_log.py` exits 0 — the `0.2.0`
  bump has a row in `spec/MIGRATIONS.md`.

## Artifacts that must exist

- `spec/payloads/<event_type>.schema.json` for all 11 declared
  event_types.
- `trace_ledger_spec/appender.py` with `append_event`.
- `examples/bad_payload.jsonl` plus an entry in the negative-
  example expectations.
- `decisions/DEC-TLS-003` and `DEC-TLS-004`.

## Out of scope for this batch

- Sqlite-backed storage. Belongs in batch `0003-storage`.
- Replay CLI. Belongs in batch `0004-replay`.
- Signing or notarization. Deferred to v0.3.
- A conformance suite. Deferred until a second implementation
  exists.

## What "done" feels like

A tool author writes a python script that imports
`trace_ledger_spec.appender.append_event`, calls it five times in a
loop with declared event_types and matching payloads, and the
resulting jsonl file passes `python -m trace_ledger_spec validate`
without further work. A second author writes the same script in
bash by shelling out to `python -m trace_ledger_spec append` and
gets the same file byte-for-byte under a pinned timestamp. The
spec is now writeable, not just readable.
