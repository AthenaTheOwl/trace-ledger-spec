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

## Gates

Built and running in CI (`.github/workflows/ci.yml`):

```bash
python -m pytest
python -m trace_ledger_spec validate      # every examples/*.jsonl; negatives expected-fail
python scripts/check_migration_log.py     # spec change => VERSION bump + MIGRATIONS row
```

`check_migration_log.py` is the load-bearing one. A change to
`spec/trace-event.schema.json` or `spec/event-types.yaml` that does not
bump `spec/VERSION` and add a row to `spec/MIGRATIONS.md` fails it, and
`spec/VERSION` must agree with the `version:` key in `event-types.yaml`.
Locally it diffs the working tree against `origin/main` (or `HEAD~1`),
so an unbumped edit fails before it is committed. Named in this file
since June 2026; built 2026-09-04.

Example validation is the reference validator itself: `python -m
trace_ledger_spec validate` loads `spec/trace-event.schema.json`,
checks every ledger under `examples/`, and treats the three planted
negatives as expected failures. The hard negative assertions live in
`tests/test_cli.py`. There is no separate `validate_examples.py` or
`validate_schemas.py`; the CLI is that gate.

Planned, not built (spec 0002): `voice_lint.py` over `spec/`, `docs/`,
and `README.md`. Do not cite it as if it runs.

## Out of scope

- Hosted ledger service. The spec plus reference implementation is
  the artifact; hosting is downstream.
- Real-time streaming primitives. The ledger is append-only batch;
  streaming compatibility is a v1 question.
- A web UI for browsing ledgers. The replay CLI plus emitted
  reports are enough for v0.
- Multi-tenant access control. Single-operator ledgers in v0.
