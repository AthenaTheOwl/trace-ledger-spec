# status

## Current state

v0.1 ships:

- `spec/trace-event.schema.json` — json schema draft 2020-12 for the
  canonical event shape, with `event_id`, `ledger_id`, `seq`,
  `timestamp`, `actor`, `event_type`, `payload`, `prev_hash` all
  required.
- `spec/event-types.yaml` — controlled vocabulary, version-pinned at
  `0.1.0`, with 11 named event types covering session lifecycle, tool
  calls, model generations, policy decisions, and ledger notes.
- `spec/VERSION` and `spec/MIGRATIONS.md` — semver discipline scaffold.
- `trace_ledger_spec/validator.py` — pure-python reference validator;
  no native deps beyond `jsonschema` and `PyYAML`.
- `trace_ledger_spec/cli.py` — `python -m trace_ledger_spec validate`
  walks `examples/*.jsonl` with no args.
- `examples/` — four ledgers: `valid.jsonl` (5 events, passes),
  `seq_gap.jsonl` (seq jumps 1 to 3), `tampered_hash.jsonl` (last
  payload altered, event_id stale), `bad_event_type.jsonl` (vocab
  violation).
- `scripts/regen_examples.py` — regenerates the example ledgers
  byte-deterministically using `validator.compute_event_id`.
- `tests/` — pytest suite with five files: `test_schema.py`,
  `test_seq.py`, `test_hash.py`, `test_vocab.py`, `test_examples.py`,
  `test_cli.py`.
- `pyproject.toml` with `[dependency-groups]` for dev deps and
  `[tool.uv]` `package = true` for the hatchling backend.

## Known limits

- no storage backend in v0.1. ledgers are jsonl files that you write
  yourself; the validator only reads them.
- no append cli. there is no `python -m trace_ledger_spec append` to
  add a new event with the chain rules pre-applied. tools that emit
  ledgers must call `compute_event_id` themselves.
- no replay cli. the validator checks structure; it does not
  re-execute past decisions under a new policy.
- the default cli behavior (walk `examples/` with no args) only works
  when invoked from a checkout or editable install. a wheel install
  from pypi has no `examples/` directory next to the package; users
  would pass an explicit path.
- the controlled vocabulary is a flat list of 11 names. there is no
  per-type payload schema yet — `payload` is any object.
- no conformance suite for second-implementation compliance.
- no signing or notarization. the chain is tamper-evident but not
  authenticated; anyone with write access could rewrite history and
  resign every event_id. signing is a v0.3 question.

## Next feature queue

ordered by smallest unblock first:

1. per-event-type payload schemas under `spec/payloads/`. lets a
   consumer know what `tool.call.completed.payload` must contain.
2. `python -m trace_ledger_spec append` cli that takes a ledger path
   and a payload, computes seq + prev_hash + event_id, and appends.
3. sqlite-backed storage adapter in `trace_ledger_spec/storage/sqlite.py`
   with the same `append` / `iterate` interface a jsonl writer would
   expose.
4. signing extension: optional `signature` field on events plus a
   verify path that checks signatures against a key set.
5. replay cli: takes a ledger plus a new policy file and a
   model-tools fingerprint; emits a typed report listing which
   decisions would have changed.
6. conformance suite: a directory of input ledgers and expected
   validator outputs that a second implementation can run to claim
   compliance with the spec at a given version.
7. wheel-install ergonomics: bundle a small set of demo ledgers
   inside the package so `python -m trace_ledger_spec validate` works
   out of the box after `pip install trace-ledger-spec`.

- Resolve factory defect: expected file 'specs/0002-design/requirements.md' is missing
- Resolve factory defect: expected file 'specs/0002-design/design.md' is missing
- Resolve factory defect: expected file 'specs/0002-design/tasks.md' is missing
- Resolve factory defect: expected file 'specs/0002-design/acceptance.md' is missing
- Resolve factory defect: claude_code review requested patch; inspect defect log
