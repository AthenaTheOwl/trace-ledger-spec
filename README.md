# trace-ledger-spec

json schema, controlled vocabulary, and reference validator for an
append-only ledger of agent trace events.

v0.1 ships the spec, the vocab, the validator, and four worked example
ledgers (one clean, three with planted bugs). later versions will add a
storage backend, a chain-verify cli, and a replay cli; see
[STATUS.md](STATUS.md).

## try it

```
python -m trace_ledger_spec report
```

```
trace-ledger-spec -- reference validator over the committed examples

ledger                ev  verdict  what it exercises                                      caught by
---------------------------------------------------------------------------------------------------
valid.jsonl            5  PASS     clean 5-event ledger; satisfies every spec rule
bad_event_type.jsonl   1  FAIL     event_type off the controlled vocabulary               vocab: event_type 'custom.not_in_vocab' not in controlled vocabulary
seq_gap.jsonl          4  FAIL     seq jumps 1->3, breaking the prev_hash chain           chain: seq gap (expected 2, got 3)
tampered_hash.jsonl    5  FAIL     payload altered; event_id no longer matches its bytes  hash: event_id mismatch (recomputed hash differs)

1 clean ledger passed, 3 planted-bug ledgers caught (vocab / chain / hash).
all examples behaved as designed.
```

read-only, no network, no args: it validates the four committed ledgers and
shows the clean one passing and each planted bug (off-vocabulary type, seq
gap, tampered payload) being caught by the rule it was meant to trip, so you
can see what the spec actually enforces before adopting it.

## live demo

the no-arg `report` verb, wrapped as an interactive page: it validates the
committed `examples/*.jsonl` ledgers and shows pass/fail per file plus the
rule that caught each planted bug. you can also paste or upload your own
ledger to validate it live. no network, no secrets.

run locally:

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

deploy on streamlit community cloud: new app -> repo
`AthenaTheOwl/trace-ledger-spec`, branch `main`, main file `streamlit_app.py`.

<!-- live url: https://<your-app>.streamlit.app -->

## what's in the box

| path                                      | what it is                                          |
|-------------------------------------------|-----------------------------------------------------|
| `spec/trace-event.schema.json`            | canonical event shape, json schema draft 2020-12.   |
| `spec/event-types.yaml`                   | version-pinned controlled vocabulary for `event_type`. |
| `spec/VERSION`                            | semver string for the published spec.               |
| `spec/MIGRATIONS.md`                      | one-row-per-change log for schema + vocab edits.    |
| `trace_ledger_spec/validator.py`          | pure-python reference validator.                    |
| `trace_ledger_spec/cli.py`                | `python -m trace_ledger_spec validate` / `report` entrypoint. |
| `examples/*.jsonl`                        | four worked ledgers: one valid, three negative.     |
| `tests/`                                  | pytest suite covering schema, seq, hash, and vocab. |
| `scripts/regen_examples.py`               | regenerate the example ledgers byte-deterministically. |

## install and run

```bash
python -m pip install -e .
python -m trace_ledger_spec validate
```

with no arguments, `validate` walks every `.jsonl` file under
`examples/` and prints `pass` or `fail` per file. three of the four
shipped ledgers are intentional negative examples, so the default
invocation exits 1. to mark those as expected failures:

```bash
python -m trace_ledger_spec validate \
  --expect-fail seq_gap.jsonl \
  --expect-fail tampered_hash.jsonl \
  --expect-fail bad_event_type.jsonl
```

to validate a specific file or directory:

```bash
python -m trace_ledger_spec validate path/to/your.jsonl
python -m trace_ledger_spec validate path/to/dir/
```

## the event shape

every event is one line of a `.jsonl` file. required fields:

| field        | type            | rule                                                   |
|--------------|-----------------|--------------------------------------------------------|
| `event_id`   | `sha256:<hex>`  | content-addressable hash of the rest of the event.     |
| `ledger_id`  | string          | constant across one ledger.                            |
| `seq`        | integer >= 0    | per-ledger monotonic, no gaps, starts at 0.            |
| `timestamp`  | rfc3339         | utc, format `date-time`.                               |
| `actor`      | object          | `{type, id, session?}` where type in {agent, human, system, tool}. |
| `event_type` | string          | drawn from `spec/event-types.yaml`.                    |
| `payload`    | object          | event-type-specific body; not constrained by schema.   |
| `prev_hash`  | `sha256:<hex>`  | event_id of the previous event; genesis is sha256:0...0. |

## validator semantics

the reference validator enforces:

1. each event matches the json schema.
2. `event_type` is listed in `spec/event-types.yaml`.
3. `event_id` equals sha256 of canonical-json of the event minus
   `event_id` itself (sorted keys, no whitespace, utf-8).
4. across a ledger: `ledger_id` is constant; `seq` starts at 0 and
   increments by 1 with no gaps; `prev_hash[n] == event_id[n-1]`,
   with the genesis prev_hash being sha256:0...0.

## tests

```bash
python -m pytest
```

covers schema validation, seq monotonicity, content-addressable hash
verification, and controlled-vocabulary enforcement. also re-validates
the committed example files so any drift between schema, hash
function, and shipped fixtures fails ci.

## related

- [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) — what this is for and what it is not.
- [SYSTEM_MAP.md](SYSTEM_MAP.md) — pieces and how they fit.
- [STATUS.md](STATUS.md) — current state, known limits, next feature queue.
- [AGENTS.md](AGENTS.md) — contract for agents working in this repo.
- [specs/0001-foundation/](specs/0001-foundation/) — the original
  requirements / design / tasks / acceptance for the foundation.

## license

mit. see [LICENSE](LICENSE).
