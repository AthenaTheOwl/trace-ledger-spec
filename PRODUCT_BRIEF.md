# product brief

## what

a published spec for storing agent trace events as an append-only,
content-addressable ledger, plus a reference validator that checks
conformance.

## who it's for

people building or auditing agent systems who need their logs to be
more than free-form strings — typed events, a tamper-evident chain,
and a controlled vocabulary so two implementations can describe the
same run in the same shape.

## what v0.1 is

- one json schema for the event shape.
- one yaml file naming the legal event types, version-pinned.
- one pure-python validator that enforces schema, hash chain, and
  vocabulary.
- a cli that runs the validator on `.jsonl` ledgers.
- four example ledgers: one valid, three with planted bugs (seq gap,
  tampered hash, unknown event_type).

## what v0.1 is not

- not a storage engine. there is no sqlite, postgres, or s3 backend.
- not a replay engine. the validator checks structure; it does not
  re-execute decisions under a new policy.
- not an observability dashboard. ledgers are jsonl on disk.
- not a hosted service. consumers run the validator themselves.
- not multi-tenant. one ledger, one writer, in v0.1.

## why the spec is the deliverable

the schema and the vocabulary are the load-bearing artifacts. if those
are right, downstream tools — storage, replay, eval, conformance suite
— can be built independently and still interoperate. shipping the
schema first, with a reference validator that proves it is checkable,
is the only way to make the spec a real spec instead of one repo's
design.

## success criteria

- a reader can open `spec/trace-event.schema.json` and
  `spec/event-types.yaml` and implement their own writer in under an
  hour.
- `python -m trace_ledger_spec validate` with no arguments runs the
  reference validator against the shipped examples and prints
  per-file pass/fail.
- the test suite catches drift between the schema, the hash function,
  and the committed example files.
- changes to the schema or vocab without a `spec/MIGRATIONS.md` row
  and a `spec/VERSION` bump are visible in code review.

## non-goals for v0.1

- second backend (postgres, s3).
- replay cli.
- chain-verify cli that operates on streaming or remote ledgers.
- conformance suite that third-party implementations can run.
- web ui.

these are tracked in [STATUS.md](STATUS.md) under "next feature queue".

## sibling-repo relationships

this repo intentionally shares its hashing discipline with receipt /
notary work elsewhere in the portfolio. event_id and prev_hash are the
same shape and the same algorithm so a ledger and a receipt log can
reference each other by content address without a translation layer.
