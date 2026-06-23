"""trace-ledger-spec CLI.

`python -m trace_ledger_spec` with no args defaults to validating every
jsonl ledger under examples/ relative to the installed package.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .validator import read_jsonl, validate_ledger

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
_DEFAULT_EXAMPLES_DIR = _REPO_ROOT / "examples"

# These bundled examples are intentional negative cases — they demonstrate the
# validator catching a tampered hash, a seq gap, and an off-vocabulary event
# type. The bare `validate` (no args) treats them as expected-fail so the first
# user action exits 0 while still showing the validator working. The hard
# negative-case assertions live in pytest.
_KNOWN_NEGATIVE_EXAMPLES = ("bad_event_type.jsonl", "seq_gap.jsonl", "tampered_hash.jsonl")

# One-line "what this example proves" used by the readable `report` verb.
# Keyed by basename. valid.jsonl is the clean control; the other three are
# the planted-bug ledgers the validator is supposed to catch.
_EXAMPLE_BLURB = {
    "valid.jsonl": "clean 5-event ledger; satisfies every spec rule",
    "bad_event_type.jsonl": "event_type off the controlled vocabulary",
    "seq_gap.jsonl": "seq jumps 1->3, breaking the prev_hash chain",
    "tampered_hash.jsonl": "payload altered; event_id no longer matches its bytes",
}

# The single rule each negative example is designed to trip. Used to label
# the catch in the report ("caught by: ...").
_EXAMPLE_RULE = {
    "bad_event_type.jsonl": "vocab",
    "seq_gap.jsonl": "chain",
    "tampered_hash.jsonl": "hash",
}


def _resolve_paths(raw_paths: list[str]) -> list[Path]:
    if raw_paths:
        out: list[Path] = []
        for p in raw_paths:
            path = Path(p)
            if path.is_dir():
                out.extend(sorted(path.glob("*.jsonl")))
            else:
                out.append(path)
        return out
    return sorted(_DEFAULT_EXAMPLES_DIR.glob("*.jsonl"))


def cmd_validate(args: argparse.Namespace) -> int:
    paths = _resolve_paths(args.paths or [])
    if not paths:
        print(f"no .jsonl files found under {_DEFAULT_EXAMPLES_DIR}", file=sys.stderr)
        return 1

    # When no explicit --expect-fail and we're walking the default examples dir,
    # the known negative cases are expected to fail so the bare first action
    # exits 0. An explicit --expect-fail overrides this default.
    if args.expect_fail:
        expect_fail = {Path(p).name for p in args.expect_fail}
    elif not (args.paths or []):
        expect_fail = set(_KNOWN_NEGATIVE_EXAMPLES)
    else:
        expect_fail = set()
    overall_ok = True

    for path in paths:
        try:
            events = read_jsonl(path)
        except (FileNotFoundError, ValueError) as exc:
            print(f"fail: {path}")
            print(f"  read: {exc}")
            overall_ok = False
            continue

        result = validate_ledger(events)
        expected_fail = path.name in expect_fail
        if result.ok:
            status = "pass" if not expected_fail else "pass (unexpected)"
            print(f"{status}: {path}")
            if expected_fail:
                overall_ok = False
        else:
            status = "fail" if not expected_fail else "fail (expected)"
            print(f"{status}: {path}")
            for err in result.errors:
                print(f"  {err}")
            if not expected_fail:
                overall_ok = False

    return 0 if overall_ok else 1


def _first_error_line(result) -> str:
    """short, path-free summary of the first error a ledger tripped.

    errors look like "event 2: chain: seq gap (expected 2, got 3)". this
    drops the "event N: " and the "<rule>: " prefixes (the rule is shown in
    its own column) and trims long hash detail so the row stays one line.
    """
    if not result.errors:
        return ""
    msg = result.errors[0]
    # strip "event N: " prefix.
    if msg.startswith("event ") and ": " in msg:
        msg = msg.split(": ", 1)[1]
    # strip the leading "<rule>: " prefix (vocab/chain/hash).
    for rule in ("vocab: ", "chain: ", "hash: "):
        if msg.startswith(rule):
            msg = msg[len(rule):]
            break
    # drop the long parenthetical hash dump; the rule + summary is enough.
    if msg.startswith("event_id mismatch"):
        msg = "event_id mismatch (recomputed hash differs)"
    return msg


def cmd_report(args: argparse.Namespace) -> int:
    """read-only, no-arg readable summary over the committed example ledgers.

    walks examples/*.jsonl, validates each, and prints a table showing the
    clean control plus the three planted-bug ledgers and which spec rule the
    validator tripped on each. exits 0 as long as the bundled set behaves as
    designed (valid passes, the three negatives fail).
    """
    paths = sorted(_DEFAULT_EXAMPLES_DIR.glob("*.jsonl"))
    if not paths:
        print(f"no .jsonl files found under {_DEFAULT_EXAMPLES_DIR}", file=sys.stderr)
        return 1
    # show the clean control first, then the planted-bug ledgers.
    paths.sort(key=lambda p: (p.name in _KNOWN_NEGATIVE_EXAMPLES, p.name))

    rows: list[tuple[str, int, str, str, str]] = []
    expected_ok = True
    for path in paths:
        name = path.name
        try:
            events = read_jsonl(path)
        except (FileNotFoundError, ValueError) as exc:
            rows.append((name, 0, "ERROR", str(exc), ""))
            expected_ok = False
            continue
        result = validate_ledger(events)
        is_negative = name in _KNOWN_NEGATIVE_EXAMPLES
        verdict = "PASS" if result.ok else "FAIL"
        # design intent: valid passes, negatives fail. flag any deviation.
        if result.ok == is_negative:
            expected_ok = False
        caught = "" if result.ok else _first_error_line(result)
        rows.append(
            (name, len(events), verdict, _EXAMPLE_BLURB.get(name, ""), caught)
        )

    name_w = max(len("ledger"), *(len(r[0]) for r in rows))
    blurb_w = max(len("what it exercises"), *(len(r[3]) for r in rows))

    print("trace-ledger-spec -- reference validator over the committed examples")
    print()
    header = (
        f"{'ledger'.ljust(name_w)}  {'ev':>2}  {'verdict':<7}  "
        f"{'what it exercises'.ljust(blurb_w)}  caught by"
    )
    print(header)
    print("-" * len(header))
    n_pass = n_fail = 0
    for name, n_ev, verdict, blurb, caught in rows:
        if verdict == "PASS":
            n_pass += 1
        else:
            n_fail += 1
        rule = _EXAMPLE_RULE.get(name, "")
        catch_col = f"{rule}: {caught}" if rule and caught else caught
        print(
            f"{name.ljust(name_w)}  {n_ev:>2}  {verdict:<7}  "
            f"{blurb.ljust(blurb_w)}  {catch_col}"
        )
    print()
    print(
        f"{n_pass} clean ledger passed, {n_fail} planted-bug ledgers caught "
        f"(vocab / chain / hash)."
    )
    if expected_ok:
        print("all examples behaved as designed.")
    else:
        print("WARNING: an example did not behave as designed.")
    return 0 if expected_ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trace-ledger-spec",
        description="reference validator for trace-ledger events.",
    )
    sub = parser.add_subparsers(dest="cmd")

    validate = sub.add_parser(
        "validate",
        help="validate one or more jsonl ledgers against schema + chain rules.",
    )
    validate.add_argument(
        "paths",
        nargs="*",
        help="paths to .jsonl files or directories. default: examples/*.jsonl",
    )
    validate.add_argument(
        "--expect-fail",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "filename(s) expected to fail validation (matched by basename). "
            "useful for negative examples in the examples/ directory."
        ),
    )
    validate.set_defaults(func=cmd_validate)

    report = sub.add_parser(
        "report",
        help=(
            "readable summary over the committed example ledgers "
            "(no args, read-only)."
        ),
    )
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["validate"]
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
