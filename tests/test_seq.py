"""seq monotonicity tests."""
from __future__ import annotations

from trace_ledger_spec.validator import (
    GENESIS_PREV_HASH,
    compute_event_id,
    validate_ledger,
)


def test_starts_at_zero(make_event):
    e = make_event(seq=1, prev_hash=GENESIS_PREV_HASH)
    result = validate_ledger([e])
    assert not result.ok
    assert any("seq" in err for err in result.errors)


def test_monotonic_no_gap(valid_chain):
    result = validate_ledger(valid_chain)
    assert result.ok, result.errors


def test_gap_in_seq_fails(valid_chain, clone):
    chain = clone(valid_chain)
    # bump seq of last event from 2 to 3, recompute its event_id so the
    # only failure is the seq gap (not a hash mismatch)
    chain[-1]["seq"] = 3
    chain[-1]["event_id"] = compute_event_id(chain[-1])
    # we also need to fix the prev_hash of the previous event, but
    # there isn't a next event after [-1], so the chain ends at this
    # tampered event. since [-1] now claims seq=3 but the expected was
    # seq=2, validation must fail with a seq gap error.
    result = validate_ledger(chain)
    assert not result.ok
    assert any("seq" in err for err in result.errors)


def test_duplicate_seq_fails(valid_chain, clone):
    chain = clone(valid_chain)
    chain[2]["seq"] = chain[1]["seq"]
    chain[2]["event_id"] = compute_event_id(chain[2])
    result = validate_ledger(chain)
    assert not result.ok
    assert any("seq" in err for err in result.errors)


def test_ledger_id_must_be_constant(valid_chain, clone):
    chain = clone(valid_chain)
    chain[1]["ledger_id"] = "different-ledger"
    chain[1]["event_id"] = compute_event_id(chain[1])
    result = validate_ledger(chain)
    assert not result.ok
    assert any("ledger_id" in err for err in result.errors)
