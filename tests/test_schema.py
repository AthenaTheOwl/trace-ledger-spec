"""schema validation tests."""
from __future__ import annotations

from trace_ledger_spec.validator import (
    GENESIS_PREV_HASH,
    compute_event_id,
    load_schema,
    validate_event,
)


def test_schema_loads():
    schema = load_schema()
    assert schema["$schema"].startswith("https://json-schema.org/")
    required = set(schema["required"])
    assert required == {
        "event_id",
        "ledger_id",
        "seq",
        "timestamp",
        "actor",
        "event_type",
        "payload",
        "prev_hash",
    }


def test_valid_event_passes(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    result = validate_event(e)
    assert result.ok, result.errors


def test_missing_required_field_fails(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    del e["timestamp"]
    result = validate_event(e)
    assert not result.ok
    assert any("timestamp" in err for err in result.errors)


def test_wrong_event_id_format_fails(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    e["event_id"] = "not-a-sha256-hash"
    result = validate_event(e)
    assert not result.ok
    assert any("event_id" in err for err in result.errors)


def test_seq_must_be_non_negative(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    e["seq"] = -1
    e["event_id"] = compute_event_id(e)
    result = validate_event(e)
    assert not result.ok
    assert any("seq" in err for err in result.errors)


def test_additional_properties_rejected(make_event):
    e = make_event(seq=0, prev_hash=GENESIS_PREV_HASH)
    e["surprise"] = "extra"
    e["event_id"] = compute_event_id(e)
    result = validate_event(e)
    assert not result.ok
    assert any("surprise" in err or "additional" in err.lower() for err in result.errors)


def test_actor_type_enum(make_event):
    e = make_event(
        seq=0,
        prev_hash=GENESIS_PREV_HASH,
        actor={"type": "alien", "id": "ufo"},
    )
    result = validate_event(e)
    assert not result.ok
    assert any("alien" in err or "enum" in err.lower() for err in result.errors)
