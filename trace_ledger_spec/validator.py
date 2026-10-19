"""reference validator for trace-ledger events.

pure-python. validates one event against the json schema, and validates
a sequence of events against the chain rules:
- seq starts at 0 and is monotonic with no gaps
- ledger_id is constant within one ledger
- prev_hash of event N equals event_id of event N-1 (genesis prev_hash
  is sha256:0...0)
- event_id equals sha256 of the canonical json of the event minus
  event_id itself
- event_type is drawn from spec/event-types.yaml
"""
from __future__ import annotations

import decimal
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

_HERE = Path(__file__).resolve().parent


def _spec_path(filename: str) -> Path:
    """resolve a spec file by checking the package-bundled copy first,
    then the repo-root spec/ directory (editable install).
    """
    bundled = _HERE / "_spec" / filename
    if bundled.exists():
        return bundled
    repo_relative = _HERE.parent / "spec" / filename
    return repo_relative


_SCHEMA_PATH = _spec_path("trace-event.schema.json")
_VOCAB_PATH = _spec_path("event-types.yaml")

GENESIS_PREV_HASH = "sha256:" + ("0" * 64)


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


def load_schema(path: Path | None = None) -> dict[str, Any]:
    target = path or _spec_path("trace-event.schema.json")
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


def load_vocab(path: Path | None = None) -> tuple[set[str], str]:
    target = path or _spec_path("event-types.yaml")
    with open(target, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = {entry["name"] for entry in data["event_types"]}
    return names, data["version"]


def canonical_bytes(event: dict[str, Any]) -> bytes:
    """canonical bytes used to compute event_id. excludes event_id itself.

    canonical form: json with sorted keys, no whitespace, utf-8 encoded.
    """
    body = {k: v for k, v in event.items() if k != "event_id"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_event_id(event: dict[str, Any]) -> str:
    digest = hashlib.sha256(canonical_bytes(event)).hexdigest()
    return f"sha256:{digest}"


def _schema_errors(event: dict[str, Any], validator: Draft202012Validator) -> list[str]:
    out: list[str] = []
    for err in sorted(validator.iter_errors(event), key=lambda e: [str(p) for p in e.path]):
        loc = "/".join(str(p) for p in err.path) or "<root>"
        out.append(f"schema: {loc}: {err.message}")
    return out


def validate_event(
    event: dict[str, Any],
    *,
    schema: dict[str, Any] | None = None,
    vocab: Iterable[str] | None = None,
) -> ValidationResult:
    """validate a single event against schema, vocab, and self-hash.

    chain rules (seq/prev_hash continuity) are not checked here; see
    validate_ledger for that.
    """
    schema = schema if schema is not None else load_schema()
    vocab = set(vocab) if vocab is not None else load_vocab()[0]
    validator = Draft202012Validator(schema)

    errors = _schema_errors(event, validator)
    if errors:
        return ValidationResult(ok=False, errors=errors)

    if event["event_type"] not in vocab:
        errors.append(
            f"vocab: event_type '{event['event_type']}' not in controlled vocabulary"
        )

    computed = compute_event_id(event)
    if event["event_id"] != computed:
        errors.append(
            f"hash: event_id mismatch (computed {computed}, got {event['event_id']})"
        )

    return ValidationResult(ok=not errors, errors=errors)


def validate_ledger(events: Iterable[dict[str, Any]]) -> ValidationResult:
    """validate a sequence of events as a single ledger.

    returns first per-event errors, then chain errors. all errors are
    collected; the first schema failure on an event short-circuits chain
    checks for that event only.
    """
    schema = load_schema()
    vocab, _ = load_vocab()
    validator = Draft202012Validator(schema)

    errors: list[str] = []
    prev_event_id = GENESIS_PREV_HASH
    expected_seq = 0
    ledger_id: str | None = None

    for idx, event in enumerate(events):
        prefix = f"event {idx}"
        schema_errs = _schema_errors(event, validator)
        if schema_errs:
            errors.extend(f"{prefix}: {e}" for e in schema_errs)
            # cannot meaningfully chain-check a malformed event.
            continue

        if ledger_id is None:
            ledger_id = event["ledger_id"]
        elif event["ledger_id"] != ledger_id:
            errors.append(
                f"{prefix}: chain: ledger_id mismatch "
                f"(expected {ledger_id}, got {event['ledger_id']})"
            )

        if event["seq"] != expected_seq:
            errors.append(
                f"{prefix}: chain: seq gap (expected {expected_seq}, got {event['seq']})"
            )

        if event["prev_hash"] != prev_event_id:
            errors.append(
                f"{prefix}: chain: prev_hash mismatch "
                f"(expected {prev_event_id}, got {event['prev_hash']})"
            )

        if event["event_type"] not in vocab:
            errors.append(
                f"{prefix}: vocab: event_type '{event['event_type']}' not in controlled vocabulary"
            )

        computed = compute_event_id(event)
        if event["event_id"] != computed:
            errors.append(
                f"{prefix}: hash: event_id mismatch "
                f"(computed {computed}, got {event['event_id']})"
            )

        prev_event_id = event["event_id"]
        expected_seq += 1

    return ValidationResult(ok=not errors, errors=errors)


class StrictJsonError(ValueError):
    """a ledger line is json that another parser could read differently."""


class DuplicateKeyError(StrictJsonError):
    """a json object on a ledger line repeats a key."""

    def __init__(self, key: str) -> None:
        super().__init__(f"duplicate key {key!r} in json object")
        self.key = key


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            raise DuplicateKeyError(key)
        obj[key] = value
    return obj


class NonFiniteNumberError(StrictJsonError):
    """a ledger line holds NaN, Infinity, or a number too large for a float."""

    def __init__(self, token: str) -> None:
        super().__init__(f"non-finite number {token!r} is not valid json")
        self.token = token


class AmbiguousNumberError(StrictJsonError):
    """a number another parser could read as a value other than the one hashed."""

    def __init__(self, token: str, reason: str) -> None:
        super().__init__(f"number {token!r} {reason}")
        self.token = token


class LoneSurrogateError(StrictJsonError):
    """a json string holds an unpaired utf-16 surrogate escape."""

    def __init__(self) -> None:
        super().__init__("unpaired utf-16 surrogate escape in a json string")


# largest integer every ieee-754 double reader holds exactly (rfc 7493 i-json).
MAX_SAFE_INTEGER = 2**53 - 1
_LONE_SURROGATE = re.compile(r"[\ud800-\udfff]")


def _reject_constant(token: str) -> Any:
    # python's json accepts the non-standard tokens NaN, Infinity and
    # -Infinity; rfc 8259 parsers reject them.
    raise NonFiniteNumberError(token)


def _parse_finite_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        # e.g. 1e400 overflows to inf and would be hashed as Infinity.
        raise NonFiniteNumberError(token)
    # canonical_bytes writes the float back with repr(). the line must
    # spell the same decimal value, or a reader that parses decimals
    # exactly sees one value while the hash covers another.
    try:
        same = decimal.Decimal(token) == decimal.Decimal(repr(value))
    except decimal.InvalidOperation:
        same = False
    if not same:
        raise AmbiguousNumberError(token, f"is hashed as {value!r}, a different value")
    return value


def _parse_safe_int(token: str) -> int:
    # more than 16 digits is always out of range; checking first also
    # keeps int() away from python's digit-count limit.
    if len(token.lstrip("-")) > 16 or abs(value := int(token)) > MAX_SAFE_INTEGER:
        raise AmbiguousNumberError(token, "is outside the interoperable range +/-(2**53 - 1)")
    if value == 0 and token.startswith("-"):
        raise AmbiguousNumberError(token, "is hashed as 0, a different value")
    return value


def _reject_lone_surrogates(value: Any) -> None:
    if isinstance(value, str):
        if _LONE_SURROGATE.search(value):
            raise LoneSurrogateError()
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_lone_surrogates(key)
            _reject_lone_surrogates(item)
    elif isinstance(value, list):
        for item in value:
            _reject_lone_surrogates(item)


def loads_event_line(text: str) -> Any:
    """parse one ledger line, rejecting anything another json parser could
    read as a different value under the same event_id.

    json parsers disagree on which value of a repeated key wins. python
    keeps the last one, so `{"args":"x","args":{...}}` would hash and
    validate here as the event without "x" while a first-wins reader acts
    on "x". the check applies to objects at every nesting level.

    also rejected, each raising a StrictJsonError:
    - NaN, Infinity, -Infinity and numbers that overflow a float.
    - a number whose decimal value differs from the canonical text it is
      hashed as: 0.10000000000000000001 (hashed as 0.1), 1e-400 (hashed
      as 0.0), -0 (hashed as 0). spellings of the same value, such as
      1.50 or 1e2, are accepted.
    - an integer outside +/-(2**53 - 1), which double-based readers round.
    - a string or key holding an unpaired utf-16 surrogate escape such as
      "\\ud800", which some readers replace with u+fffd.
    """
    value = json.loads(
        text,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
        parse_float=_parse_finite_float,
        parse_int=_parse_safe_int,
    )
    _reject_lone_surrogates(value)
    return value


def parse_jsonl(lines: Iterable[str], source: str) -> list[dict[str, Any]]:
    """parse ledger lines with loads_event_line, skipping blank lines.

    errors read "<source>:<line>: invalid json: <reason>". pass a text
    file object, or io.StringIO(text, newline=None) for in-memory text, so
    lines split only at newlines and never at u+2028 or other characters
    str.splitlines() treats as breaks.
    """
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            events.append(loads_event_line(stripped))
        except (json.JSONDecodeError, StrictJsonError) as exc:
            raise ValueError(f"{source}:{lineno}: invalid json: {exc}") from exc
    return events


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return parse_jsonl(f, str(path))
