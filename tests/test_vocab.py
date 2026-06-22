"""controlled-vocabulary enforcement tests."""
from __future__ import annotations

from trace_ledger_spec.validator import (
    GENESIS_PREV_HASH,
    compute_event_id,
    load_vocab,
    validate_event,
)


def test_vocab_loads():
    names, version = load_vocab()
    assert version == "0.1.0"
    assert "session.start" in names
    assert "tool.call.completed" in names
    assert "policy.decision.evaluated" in names


def test_known_event_type_passes(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH, event_type="ledger.note")
    result = validate_event(e)
    assert result.ok, result.errors


def test_unknown_event_type_fails(make_event):
    e = make_event(
        seq=0,
        prev_hash=GENESIS_PREV_HASH,
        event_type="custom.not_in_vocab",
    )
    result = validate_event(e)
    assert not result.ok
    assert any("vocab" in err for err in result.errors)


def test_every_vocab_entry_validates(make_event):
    names, _ = load_vocab()
    for name in names:
        e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH, event_type=name)
        result = validate_event(e)
        assert result.ok, (name, result.errors)
