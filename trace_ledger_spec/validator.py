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

import hashlib
import json
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                events.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid json: {exc}") from exc
    return events
