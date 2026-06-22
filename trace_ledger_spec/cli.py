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
