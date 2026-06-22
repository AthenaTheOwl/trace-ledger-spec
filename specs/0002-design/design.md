# Design — Design batch

This batch turns `event_type` from a name into a name-plus-shape, and
turns the validator into a writer. After it lands, a tool emitting a
ledger no longer needs to know the canonical-bytes recipe — it shells
out to `python -m trace_ledger_spec append`.

## Shape

```
spec/event-types.yaml                  (list of names)
spec/payloads/                         (one schema per name)
  session.start.schema.json
  session.checkpoint.schema.json
  session.end.schema.json
  tool.call.requested.schema.json
  tool.call.completed.schema.json
  tool.call.failed.schema.json
  model.generation.requested.schema.json
  model.generation.completed.schema.json
  policy.decision.evaluated.schema.json
  policy.decision.overridden.schema.json
  ledger.note.schema.json

trace_ledger_spec/
  validator.py                         (loads + applies payload schemas)
  cli.py
    validate (existing, now also checks payloads)
    append   (new)
  appender.py                          (new; pure-python writer)
```

## Per-type payload loading

`validator.load_payload_schemas()` walks `spec/payloads/*.schema.json`,
keyed by the schema's `$id` final path component (matching the
event_type name). The mapping is built once per process and cached on
the module. `validate_event` looks up the schema by `event_type` and
validates `payload` against it after the top-level schema pass.

A payload schema looks like:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://traceledger.dev/spec/v0.1/payloads/tool.call.completed.schema.json",
  "title": "tool.call.completed",
  "type": "object",
  "additionalProperties": false,
  "required": ["tool", "result_ref"],
  "properties": {
    "tool":       {"type": "string", "minLength": 1},
    "args":       {"type": "object"},
    "result_ref": {"type": "string"},
    "latency_ms": {"type": "integer", "minimum": 0}
  }
}
```

The validator surfaces payload errors as
`event <i>: payload: <field>: <message>`.

## Append CLI

```
python -m trace_ledger_spec append <ledger.jsonl> \
    --type tool.call.completed \
    --payload @payload.json \
    --actor-type agent \
    --actor-id supplier-risk-rag-agent@v0.4.2 \
    [--session 01HX7B3J5K2-session-3] \
    [--timestamp 2026-06-22T14:00:00Z]
```

Steps the appender takes, in order:

1. read existing `<ledger.jsonl>` (may be empty / missing).
2. derive `seq = len(existing)`, `prev_hash = last.event_id` or
   genesis.
3. load `ledger_id` from the existing ledger; if missing, require
   `--ledger-id` on the call.
4. assemble the event dict minus `event_id`.
5. compute `event_id = compute_event_id(event)`.
6. run `validate_event` on the assembled event. on failure: print
   errors, exit 1, do not touch the file.
7. acquire `<ledger>.lock` via O_EXCL create; release on exit.
8. append the json line atomically (write to temp, fsync, rename
   into place is overkill for jsonl; a single append with fsync is
   fine).

`--payload @file` reads json from `file`. `--payload <inline>` parses
the argv string as json.

## Why an `append` command instead of a library API

A library API exists: `trace_ledger_spec.appender.append_event()`.
The CLI is a thin wrapper. We ship both because most ledger emitters
in the wild are bash scripts, log-shippers, or non-python tools that
can shell out but cannot import; and tests / examples want the
library form.

## Why a lockfile and not flock

Cross-platform. The repo already targets windows + linux + macos.
`os.O_EXCL` create works on all three. The lockfile contains the
PID so a stale lock can be inspected and removed by a human.

## Deterministic example regeneration

`scripts/regen_examples.py` already exists and computes event_ids
by hand. After this batch it switches to calling
`appender.append_event()` with a pinned `--timestamp`, which makes
the script smaller and tied to the same code path the CLI uses.

## Dependencies

No new runtime deps. `jsonschema` and `pyyaml` already pinned in
`pyproject.toml`. Lockfile uses stdlib `os.open` with `O_EXCL`.

## What is deliberately NOT in this batch

- Sqlite or other storage backends. The next batch (`0003-storage`)
  picks those up.
- Replay. Same reason.
- Signing. Deferred to v0.3.
- A conformance suite. Cannot be honest about conformance until a
  second implementation exists.
