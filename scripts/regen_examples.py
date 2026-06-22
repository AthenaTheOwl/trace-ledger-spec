"""regenerate example jsonl ledgers under examples/.

four files:
- valid.jsonl: a clean 5-event ledger that passes all checks.
- seq_gap.jsonl: same chain but event with seq=2 is dropped, so seq
  jumps 0,1,3,4 and the prev_hash for the seq=3 event no longer
  matches the previous in-file event.
- tampered_hash.jsonl: the last event's payload is altered after the
  fact so its event_id no longer matches its canonical bytes.
- bad_event_type.jsonl: a single event whose event_type is not in the
  controlled vocabulary.

deterministic: rerunning produces byte-identical output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from trace_ledger_spec.validator import GENESIS_PREV_HASH, compute_event_id  # noqa: E402

EXAMPLES_DIR = _HERE.parent / "examples"
LEDGER_ID = "01HZTRACELEDGEREXAMPLE01"


def make_event(seq: int, prev_hash: str, event_type: str, payload: dict, timestamp: str, actor_id: str) -> dict:
    # build actor in alphabetical key order for stable serialized output
    actor = {
        "id": actor_id,
        "session": f"{LEDGER_ID}-session-1",
        "type": "agent",
    }
    event = {
        "ledger_id": LEDGER_ID,
        "seq": seq,
        "timestamp": timestamp,
        "actor": actor,
        "event_type": event_type,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    event_id = compute_event_id(event)
    return {
        "event_id": event_id,
        "ledger_id": event["ledger_id"],
        "seq": event["seq"],
        "timestamp": event["timestamp"],
        "actor": event["actor"],
        "event_type": event["event_type"],
        "payload": event["payload"],
        "prev_hash": event["prev_hash"],
    }


def build_ledger() -> list[dict]:
    actor = "example-agent@v0.1.0"
    timestamps = [
        "2026-06-22T10:00:00.000Z",
        "2026-06-22T10:00:01.120Z",
        "2026-06-22T10:00:02.480Z",
        "2026-06-22T10:00:03.510Z",
        "2026-06-22T10:00:04.770Z",
    ]
    events: list[dict] = []
    prev = GENESIS_PREV_HASH
    # payload keys held in alphabetical order so json.dumps with
    # sort_keys=False matches the committed files byte-for-byte.
    specs = [
        ("session.start", {"session_id": f"{LEDGER_ID}-session-1"}),
        ("tool.call.requested", {"args": {"q": "trace ledger v0"}, "tool": "search"}),
        ("tool.call.completed", {"latency_ms": 184, "result_ref": "blob://sha256:deadbeef", "tool": "search"}),
        ("policy.decision.evaluated", {"decision": "allow", "policy": "refusal_v1"}),
        ("session.end", {"reason": "completed"}),
    ]
    for i, (et, payload) in enumerate(specs):
        ev = make_event(i, prev, et, payload, timestamps[i], actor)
        events.append(ev)
        prev = ev["event_id"]
    return events


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for ev in events:
            f.write(json.dumps(ev, separators=(",", ":"), sort_keys=False))
            f.write("\n")


def build_bad_event_type() -> list[dict]:
    actor = {
        "id": "example-agent@v0.1.0",
        "session": "01HZTRACELEDGEREXAMPLE02-session-1",
        "type": "agent",
    }
    event = {
        "ledger_id": "01HZTRACELEDGEREXAMPLE02",
        "seq": 0,
        "timestamp": "2026-06-22T11:00:00.000Z",
        "actor": actor,
        "event_type": "custom.not_in_vocab",
        "payload": {"note": "this event_type is not registered"},
        "prev_hash": GENESIS_PREV_HASH,
    }
    event_id = compute_event_id(event)
    return [{
        "event_id": event_id,
        "ledger_id": event["ledger_id"],
        "seq": event["seq"],
        "timestamp": event["timestamp"],
        "actor": event["actor"],
        "event_type": event["event_type"],
        "payload": event["payload"],
        "prev_hash": event["prev_hash"],
    }]


def main() -> None:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    valid = build_ledger()
    write_jsonl(EXAMPLES_DIR / "valid.jsonl", valid)

    # seq_gap: drop event with seq=2 so the file contains seq 0,1,3,4.
    gapped = [valid[0], valid[1], valid[3], valid[4]]
    write_jsonl(EXAMPLES_DIR / "seq_gap.jsonl", gapped)

    # tampered_hash: alter the payload of the last event without
    # recomputing event_id. validator should flag a hash mismatch.
    tampered = [dict(ev) for ev in valid]
    last = dict(tampered[-1])
    last["payload"] = dict(last["payload"])
    last["payload"]["reason"] = "TAMPERED"
    tampered[-1] = last
    write_jsonl(EXAMPLES_DIR / "tampered_hash.jsonl", tampered)

    write_jsonl(EXAMPLES_DIR / "bad_event_type.jsonl", build_bad_event_type())

    print(f"wrote 4 example ledgers under {EXAMPLES_DIR}")


if __name__ == "__main__":
    main()
