# system map

how the pieces fit, top to bottom.

```
spec/                              <-- the published spec, top-level by intent
  trace-event.schema.json          <-- json schema draft 2020-12, the machine shape
  event-types.yaml                 <-- controlled vocabulary, version-pinned
  VERSION                          <-- semver string
  MIGRATIONS.md                    <-- one-row-per-change log
        |
        |  loaded by
        v
trace_ledger_spec/                 <-- the reference validator (python package)
  validator.py                     <-- pure-python validation logic
    load_schema()                  <-- reads spec/trace-event.schema.json
    load_vocab()                   <-- reads spec/event-types.yaml
    canonical_bytes(event)         <-- sorted-key json minus event_id, utf-8
    compute_event_id(event)        <-- "sha256:" + sha256(canonical_bytes)
    validate_event(event)          <-- schema + vocab + self-hash for one event
    validate_ledger(events)        <-- per-event checks + chain checks across events
  cli.py                           <-- argparse cli
    validate                       <-- default subcommand
  __main__.py                      <-- "python -m trace_ledger_spec"
        |
        |  called by
        v
examples/*.jsonl                   <-- four worked ledgers (one valid, three negative)
tests/test_*.py                    <-- pytest suite
scripts/regen_examples.py          <-- regenerates examples/ deterministically
```

## responsibilities

| component        | responsible for                                            | not responsible for                                  |
|------------------|------------------------------------------------------------|------------------------------------------------------|
| `spec/`          | being the authoritative machine + human shape.             | any python; consumable from any language.            |
| `validator.py`   | enforcing every rule named in the spec.                    | storage, replay, streaming, network transport.       |
| `cli.py`         | a thin wrapper that walks files and prints results.        | parsing or validation logic; just orchestration.     |
| `examples/`      | demonstrating one passing and three failing ledger shapes. | covering every possible event_type or edge case.    |
| `tests/`         | catching drift between schema, hash, and committed fixtures. | end-to-end runtime testing.                         |
| `scripts/regen_examples.py` | making the example files reproducible.          | doubling as a library; tests use it for setup only.  |

## chain rule (the load-bearing invariant)

```
event[n].prev_hash == event[n-1].event_id       for n >= 1
event[0].prev_hash == sha256:0...0              (genesis)
event[n].seq == n                                (monotonic from 0, no gaps)
event[n].event_id == sha256(canonical(event[n] - event_id))
event[n].ledger_id == event[0].ledger_id        (constant per ledger)
```

if any field of any past event changes, the recomputed event_id
changes, and every downstream prev_hash check fails at the altered
point. that is what makes the ledger tamper-evident without a signing
key.

## boundaries with sibling repos

this repo deliberately publishes only the event schema and validator.
it does not ship:

- a storage backend (deferred; see STATUS.md).
- a receipt schema (handled by a sibling notary spec; uses the same
  hash discipline so the two compose).
- a replay engine (deferred; needs the storage backend first).

other tools that want to consume trace-ledger ledgers import this
package's `validator.validate_ledger` to confirm the input conforms
before they touch it.
