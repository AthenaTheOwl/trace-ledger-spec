"""example-file tests: the committed jsonl ledgers under examples/.

these verify the precomputed hashes match the validator's expectations,
so any drift between the schema, hash function, and committed fixtures
is caught.
"""
from __future__ import annotations

from trace_ledger_spec.validator import read_jsonl, validate_ledger


def test_valid_example_passes(examples_dir):
    events = read_jsonl(examples_dir / "valid.jsonl")
    assert len(events) == 5
    result = validate_ledger(events)
    assert result.ok, result.errors


def test_seq_gap_example_fails(examples_dir):
    events = read_jsonl(examples_dir / "seq_gap.jsonl")
    result = validate_ledger(events)
    assert not result.ok
    assert any("seq" in err for err in result.errors)


def test_tampered_example_fails(examples_dir):
    events = read_jsonl(examples_dir / "tampered_hash.jsonl")
    result = validate_ledger(events)
    assert not result.ok
    assert any("hash" in err or "event_id" in err for err in result.errors)


def test_bad_event_type_example_fails(examples_dir):
    events = read_jsonl(examples_dir / "bad_event_type.jsonl")
    result = validate_ledger(events)
    assert not result.ok
    assert any("vocab" in err for err in result.errors)
