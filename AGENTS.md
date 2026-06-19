# AGENTS.md — trace-ledger-spec

Operating contract for AI agents working in this repo. Conventions
match the rest of the AthenaTheOwl portfolio.

## What this repo is

The trace-ledger spec, schema, reference implementation, and
conformance suite. The spec is the load-bearing artifact. The
SQLite reference exists to prove the spec is implementable. The
conformance suite exists so a second implementation can claim
compliance.

Anything that changes spec/ requires a corresponding RFC update and
a DEC record. Spec changes are sticky; they ripple to every
downstream consumer.

## Roles you may see in tasks

| Role | What they do |
|---|---|
| `spec-author` | Maintains `spec/trace-event.schema.json` and RFC docs |
| `reference-engineer` | Builds the SQLite-backed ledger and replay CLI |
| `example-curator` | Hand-curates worked example streams under examples/ |
| `conformance-author` | Writes the test suite for second-implementation compliance |
| `migration-tracker` | Records every spec change in MIGRATIONS.md |

These roles exist in spec ledger; not all are implemented in v0.

## Voice constraints

- The RFC is the customer surface. Read it through voice_lint
  before each commit.
- No marketing words. The spec speaks for itself.
- No antithetical-reversal phrasing.
- Spec language is RFC-2119 normative (MUST / SHOULD / MAY). Prose
  around it is plain English.

## Gates (will land in spec 0002)

```bash
python -m pytest
python scripts/voice_lint.py spec/ docs/ README.md
python scripts/validate_schemas.py spec/
python scripts/validate_examples.py examples/
python scripts/check_migration_log.py
```

The `check_migration_log.py` gate is the load-bearing one. A spec
change that does not bump the version in `spec/VERSION` and add a
row to `spec/MIGRATIONS.md` fails the gate.

## Out of scope

- Hosted ledger service. The spec plus reference implementation is
  the artifact; hosting is downstream.
- Real-time streaming primitives. The ledger is append-only batch;
  streaming compatibility is a v1 question.
- A web UI for browsing ledgers. The replay CLI plus emitted
  reports are enough for v0.
- Multi-tenant access control. Single-operator ledgers in v0.
