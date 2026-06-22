"""cli tests: `python -m trace_ledger_spec` behavior."""
from __future__ import annotations

from trace_ledger_spec.cli import main


def test_no_args_runs_validate_on_examples(capsys):
    rc = main([])
    captured = capsys.readouterr().out
    assert "valid.jsonl" in captured
    # bare `validate` (no args) treats the bundled negative examples as
    # expected-fail, so the first user action exits 0 while still showing the
    # validator catching the tamper / gap / vocab cases.
    assert "fail (expected)" in captured
    assert rc == 0


def test_expect_fail_flags_make_negative_examples_pass(capsys):
    rc = main([
        "validate",
        "--expect-fail",
        "seq_gap.jsonl",
        "--expect-fail",
        "tampered_hash.jsonl",
        "--expect-fail",
        "bad_event_type.jsonl",
    ])
    out = capsys.readouterr().out
    assert "fail (expected)" in out
    assert rc == 0


def test_validate_specific_file(capsys, examples_dir):
    rc = main(["validate", str(examples_dir / "valid.jsonl")])
    assert rc == 0


def test_validate_nonexistent_file_fails(capsys, tmp_path):
    rc = main(["validate", str(tmp_path / "missing.jsonl")])
    assert rc != 0
