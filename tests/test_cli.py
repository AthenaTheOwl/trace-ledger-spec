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


def test_report_summarizes_examples_and_exits_zero(capsys):
    rc = main(["report"])
    out = capsys.readouterr().out
    # the clean control and all three planted-bug ledgers are listed.
    assert "valid.jsonl" in out
    assert "bad_event_type.jsonl" in out
    assert "seq_gap.jsonl" in out
    assert "tampered_hash.jsonl" in out
    # the verdict column and the per-rule catch labels are present.
    assert "PASS" in out
    assert "FAIL" in out
    assert "vocab" in out and "chain" in out and "hash" in out
    assert "1 clean ledger passed, 3 planted-bug ledgers caught" in out
    assert "all examples behaved as designed." in out
    # report is read-only over a known-good fixture set; it exits 0.
    assert rc == 0
