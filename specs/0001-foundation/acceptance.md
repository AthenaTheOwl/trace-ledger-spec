# Acceptance — v0 Foundation

"v0 done" means the spec is published, the SQLite reference
implements it, the replay CLI works on a worked example, and the
migration log gate refuses spec changes that skip versioning.

## Commands a reviewer must be able to run

```bash
python -m pip install -e .[dev]

python -m trace_ledger init runs/example.db

for f in examples/minimal/events/*.json; do
  python -m trace_ledger append runs/example.db --event "$f"
done

python -m trace_ledger verify runs/example.db

python -m trace_ledger replay runs/example.db \
  --policy examples/minimal/policies/refusal_v2.yaml \
  --out reports/replay.json
```

## Gates that must pass

- `python -m pytest` exits 0.
- `python scripts/voice_lint.py spec/ docs/ README.md` exits 0.
- `python scripts/validate_schemas.py spec/` exits 0.
- `python scripts/validate_examples.py examples/` exits 0 — every
  example event validates and every example ledger's chain
  verifies.
- `python scripts/check_migration_log.py` exits 0.

## Artifacts that must exist

- `spec/trace-event.schema.json`, `spec/event-types.yaml`,
  `spec/RFC-001-trace-event-format.md`, `spec/VERSION`,
  `spec/MIGRATIONS.md`.
- `examples/minimal/` (5 hand-crafted events).
- `examples/procurement-negotiation-lab/` (a real ledger, ~230
  events).
- `decisions/DEC-TLS-001` and `DEC-TLS-002`.

## Out of scope for v0

- A second backend implementation.
- A formal conformance suite for third-party implementations.
- Multi-tenant access control.
- Real-time streaming append APIs.
- A web UI.

## What "done" feels like

A platform engineer reads `spec/RFC-001` once, opens
`spec/trace-event.schema.json`, and could implement a Postgres-
backed ledger in a weekend. They run the replay CLI against the
worked example, get a deterministic report, and trust the chain.
The spec is small enough to hold in working memory and complete
enough to govern real behavior. That is the bar.
