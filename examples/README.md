# examples

four jsonl ledgers used by the reference validator and the test suite.
each line is one event matching `spec/trace-event.schema.json`.

| file                  | expected | what it shows                                              |
|-----------------------|----------|------------------------------------------------------------|
| `valid.jsonl`         | pass     | a 5-event ledger that satisfies every spec rule.           |
| `seq_gap.jsonl`       | fail     | seq jumps from 1 to 3; also breaks the prev_hash chain.    |
| `tampered_hash.jsonl` | fail     | the last event's payload was altered; event_id no longer matches its canonical bytes. |
| `bad_event_type.jsonl`| fail     | one event uses an event_type not in `spec/event-types.yaml`. |

to regenerate from source: `python scripts/regen_examples.py`.
the script rewrites these four files byte-deterministically.

to validate from the cli:

```
python -m trace_ledger_spec validate
```

which exits 1 because three of four ledgers are intentional fails. to
mark them as expected failures and exit 0 on the curated set:

```
python -m trace_ledger_spec validate --expect-fail seq_gap.jsonl \
  --expect-fail tampered_hash.jsonl --expect-fail bad_event_type.jsonl
```
