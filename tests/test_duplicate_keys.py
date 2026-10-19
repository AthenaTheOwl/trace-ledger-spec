"""strict-read tests: duplicate object keys and non-finite numbers on a ledger line.

json parsers disagree on which value of a repeated key wins. python keeps
the last one, so an extra "args" placed ahead of the real key leaves the
parsed event, its canonical bytes, and the hash chain unchanged while a
first-wins reader of the same file sees the injected value.
"""
from __future__ import annotations

import io
import json

import pytest

from trace_ledger_spec.cli import main
from trace_ledger_spec.validator import (
    compute_event_id,
    parse_jsonl,
    read_jsonl,
    validate_ledger,
)

_REAL_ARGS = '"payload":{"args":{"q":"trace ledger v0"}'
_INJECTED_ARGS = '"payload":{"args":"INJECTED","args":{"q":"trace ledger v0"}'


@pytest.fixture
def injected_ledger(examples_dir, tmp_path):
    """valid.jsonl with "args":"INJECTED" ahead of the real key on line 2."""
    text = (examples_dir / "valid.jsonl").read_text(encoding="utf-8")
    assert text.count(_REAL_ARGS) == 1
    path = tmp_path / "dup_args.jsonl"
    path.write_text(text.replace(_REAL_ARGS, _INJECTED_ARGS), encoding="utf-8")
    return path


def test_injected_key_is_invisible_to_a_last_wins_parse(injected_ledger):
    # the attack: parsed last-wins, the edited file still validates with
    # the committed head, so the hash chain alone cannot catch it.
    lines = injected_ledger.read_text(encoding="utf-8").splitlines()
    assert validate_ledger([json.loads(line) for line in lines]).ok


def test_read_jsonl_rejects_injected_duplicate_key(injected_ledger):
    with pytest.raises(ValueError, match=r"dup_args\.jsonl:2: .*duplicate key 'args'"):
        read_jsonl(injected_ledger)


def test_validate_fails_on_injected_duplicate_key(injected_ledger, capsys):
    rc = main(["validate", str(injected_ledger)])
    out = capsys.readouterr().out
    assert rc == 1
    assert f"fail: {injected_ledger}" in out
    assert "duplicate key 'args'" in out


@pytest.mark.parametrize(
    "line, key",
    [
        ('{"seq":0,"seq":1}', "seq"),
        ('{"payload":{"tool":"a","tool":"b"}}', "tool"),
        ('{"payload":{"args":{"q":"a","q":"b"}}}', "q"),
        ('{"payload":{"items":[{"k":1,"k":2}]}}', "k"),
    ],
)
def test_duplicate_key_rejected_at_every_nesting_level(tmp_path, line, key):
    path = tmp_path / "dup.jsonl"
    path.write_text(line + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=rf"dup\.jsonl:1: .*duplicate key '{key}'"):
        read_jsonl(path)


def test_same_key_in_sibling_objects_is_allowed(tmp_path):
    path = tmp_path / "siblings.jsonl"
    path.write_text('{"a":{"k":1},"b":{"k":2}}\n', encoding="utf-8")
    assert read_jsonl(path) == [{"a": {"k": 1}, "b": {"k": 2}}]


@pytest.mark.parametrize(
    "line, token",
    [
        ('{"payload":{"x":NaN}}', "NaN"),
        ('{"payload":{"x":Infinity}}', "Infinity"),
        ('{"payload":{"x":[-Infinity]}}', "-Infinity"),
        ('{"payload":{"x":1e400}}', "1e400"),
    ],
)
def test_non_finite_number_rejected(tmp_path, line, token):
    path = tmp_path / "nonfinite.jsonl"
    path.write_text(line + "\n", encoding="utf-8")
    with pytest.raises(
        ValueError, match=rf"nonfinite\.jsonl:1: .*non-finite number '{token}'"
    ):
        read_jsonl(path)


def test_sealed_nan_ledger_fails_validate(examples_dir, tmp_path, capsys):
    # a ledger sealed over NaN still hashes consistently, so only the
    # reader can catch it.
    first = json.loads((examples_dir / "valid.jsonl").read_text("utf-8").splitlines()[0])
    first["payload"] = {"x": float("nan")}
    del first["event_id"]
    first["event_id"] = compute_event_id(first)
    path = tmp_path / "nan.jsonl"
    path.write_text(json.dumps(first) + "\n", encoding="utf-8")
    assert "NaN" in path.read_text("utf-8")
    rc = main(["validate", str(path)])
    assert rc == 1
    assert "non-finite number 'NaN'" in capsys.readouterr().out


def test_parse_jsonl_splits_only_at_newlines(examples_dir):
    # u+2028 is legal raw inside a json string; str.splitlines() breaks on it.
    first = json.loads((examples_dir / "valid.jsonl").read_text("utf-8").splitlines()[0])
    first["payload"] = {"s": "a b"}
    del first["event_id"]
    first["event_id"] = compute_event_id(first)
    text = json.dumps(first, ensure_ascii=False) + "\r\n"
    assert " " in text
    events = parse_jsonl(io.StringIO(text, newline=None), "pasted")
    assert validate_ledger(events).ok


def test_parse_jsonl_names_source_line_and_key():
    text = '{"a":1}\n\n{"k":1,"k":2}\n'
    with pytest.raises(ValueError, match=r"^pasted:3: invalid json: duplicate key 'k'"):
        parse_jsonl(io.StringIO(text, newline=None), "pasted")
