# TraceLedger Spec

An open specification and reference implementation for an append-only
event ledger storing agent traces with enough structure that you can
replay any decision, regress any policy, and compute any eval against
historical logs.

## What this is

LangSmith, Logfire, and Weights & Biases ship observability
dashboards on top of agent traces. None of them ship an append-only
ledger with replay-friendly semantics. The CDCP operating-model memo
plus the 22-step lifecycle name this gap as load-bearing. The EU AI
Act Article 12 and NIST AI RMF 1.1 require auditability that current
dashboards do not structurally provide.

This repo is the spec, the schema, the SQLite reference
implementation, the replay CLI, and one worked example replaying a
`procurement-negotiation-lab` session.

## Status

v0 scaffold. No implementation yet. Specs in `specs/0001-foundation/`
name the event schema, the append-only invariants, and the replay
semantics. PR 0002 lands `spec/trace-event.schema.json` plus the
RFC-001 document.

## How to run

Placeholder. Will land in spec 0003. The intended invocation:

```bash
python -m trace_ledger init runs/example.db
python -m trace_ledger append runs/example.db \
  --event examples/events/01_session_start.json
python -m trace_ledger replay runs/example.db \
  --policy policies/refusal_v2.yaml \
  --out reports/replay.json
python -m trace_ledger eval runs/example.db \
  --pack ../eval-forge/templates/agent/eval_pack.yaml \
  --out reports/eval.json
```

## Layout

```
trace-ledger-spec/
  README.md
  LICENSE
  AGENTS.md
  .gitignore
  specs/
    0001-foundation/
      requirements.md
      design.md
      tasks.md
      acceptance.md
  docs/
    first-pr.md
  spec/                  # schema + RFC docs; arrives in PR 0002
  examples/              # worked event streams
  src/                   # arrives in PR 0003
```

## Why this exists

CDCP discipline says traces are typed artifacts, not log strings.
The `factory/` orchestrator's event-emission pattern in
`procurement-negotiation-lab` and the
`ops/event-log/YYYY-MM-DD.jsonl` design from the operating-model
memo are working prototypes of what this spec formalizes. Nobody
else's framing matches what the regulators (EU AI Act, NIST RMF)
actually ask for.

## Three layered claims

The repo makes three claims, layered:

1. *Spec.* `trace-event.schema.json` plus RFC-001 are sufficient to
   describe any agent run such that another tool can re-derive the
   run's decisions.
2. *Reference implementation.* A SQLite-backed append-only ledger
   matches the spec and supports replay + eval against historical
   ledgers.
3. *Conformance.* A conformance test suite that other implementations
   (Postgres, S3, custom) can run to claim spec compliance.

v0 ships claim 1 and claim 2. Claim 3 is a near-term follow-on.

## Sibling to

- `agent-notary-layer` (receipt schema; they package together as
  "Agent Audit Infrastructure")
- `trace-to-eval-harness` (the literal prototype this productizes)
- `eval-forge` (consumes ledgers for replay-based eval gates)
- `dream-replay-cli` (consumes ledgers as a primary input source)

## License

MIT. See [LICENSE](LICENSE).
