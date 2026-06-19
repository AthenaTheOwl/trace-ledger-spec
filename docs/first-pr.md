# First PR (after scaffold)

The literal first PR after this v0 scaffold is PR 0002: the spec,
the RFC, and the event-type vocabulary. No code yet — just the
typed shape.

## Scope

One PR. The spec is the load-bearing artifact; the reference
implementation that lands in PR 0003 must conform to it. Get the
spec right first.

## Files added

```
spec/trace-event.schema.json
spec/event-types.yaml
spec/VERSION
spec/MIGRATIONS.md
spec/RFC-001-trace-event-format.md
scripts/voice_lint.py
scripts/validate_schemas.py
scripts/validate_examples.py
scripts/check_migration_log.py
examples/minimal/events/01_session_start.json
examples/minimal/events/02_tool_call_completed.json
examples/minimal/events/03_policy_decision_evaluated.json
examples/minimal/events/04_session_checkpoint.json
examples/minimal/events/05_session_end.json
tests/test_schema_validates.py
tests/test_examples_validate.py
pyproject.toml
```

## Files changed

```
README.md         # "How to run" gets the validate commands
AGENTS.md         # uncomment the gate block
```

## Why this scope

The event schema, the controlled event-type vocabulary, and the RFC
form a unit. They must ship together: the schema without the
vocabulary is too permissive; the vocabulary without the RFC has no
normative weight; the RFC without the schema cannot be machine-
checked.

The five minimal hand-crafted examples cover the five most-common
event-type shapes the spec needs to support: session lifecycle,
tool call completion, policy decision evaluation, session
checkpoint, session end. Each example is short enough to read
through in one screen and validates against the schema cleanly.

## Verification

```bash
python -m pip install -e .[dev]
python -m pytest
python scripts/voice_lint.py README.md AGENTS.md spec/
python scripts/validate_schemas.py spec/
python scripts/validate_examples.py examples/minimal/
python scripts/check_migration_log.py
```

All five exit 0. `spec/VERSION` reads `0.1.0`.
`spec/MIGRATIONS.md` has one row noting the initial draft.

## Out of scope (deferred to PR 0003)

- The SQLite reference ledger.
- The append CLI.
- The verify CLI (chain check).
- The replay CLI.

## Decision record

PR 0002 lands `decisions/DEC-TLS-000-rfc-2119-normative-spec.md`
naming why the spec is written in RFC-2119 normative language with
the JSON Schema as the machine-readable shadow — making the spec
testable against any implementation, not just the reference one.
