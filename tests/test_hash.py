"""content-addressable event_id and prev_hash chain tests."""
from __future__ import annotations

import hashlib

from trace_ledger_spec.validator import (
    GENESIS_PREV_HASH,
    canonical_bytes,
    compute_event_id,
    validate_event,
    validate_ledger,
)


def test_genesis_prev_hash_format():
    assert GENESIS_PREV_HASH == "sha256:" + ("0" * 64)


def test_event_id_excludes_self(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    body = canonical_bytes(e)
    assert b"event_id" not in body


def test_event_id_is_sha256_of_canonical(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    expected = "sha256:" + hashlib.sha256(canonical_bytes(e)).hexdigest()
    assert e["event_id"] == expected


def test_tampered_payload_breaks_self_hash(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH, payload={"safe": True})
    e["payload"]["safe"] = False  # tamper without recomputing event_id
    result = validate_event(e)
    assert not result.ok
    assert any("hash" in err or "event_id" in err for err in result.errors)


def test_tampered_event_in_chain_breaks_downstream(valid_chain, clone):
    chain = clone(valid_chain)
    # tamper event 0's payload without recomputing event_id. validator
    # should flag the hash mismatch at event 0 AND a prev_hash mismatch
    # at event 1 (since event 1's prev_hash referenced the original
    # event_id which would have changed under any honest recomputation).
    chain[0]["payload"] = {"tampered": True}
    result = validate_ledger(chain)
    assert not result.ok
    assert any("hash" in err for err in result.errors)


def test_recomputed_chain_validates(valid_chain):
    result = validate_ledger(valid_chain)
    assert result.ok, result.errors


def test_bad_prev_hash_fails(valid_chain, clone):
    chain = clone(valid_chain)
    chain[1]["prev_hash"] = "sha256:" + ("a" * 64)
    chain[1]["event_id"] = compute_event_id(chain[1])
    # recompute downstream so the only failure is the prev_hash mismatch
    chain[2]["prev_hash"] = chain[1]["event_id"]
    chain[2]["event_id"] = compute_event_id(chain[2])
    result = validate_ledger(chain)
    assert not result.ok
    assert any("prev_hash" in err for err in result.errors)
