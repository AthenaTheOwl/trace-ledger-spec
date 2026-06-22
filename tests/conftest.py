"""shared fixtures for trace-ledger-spec tests."""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from trace_ledger_spec.validator import GENESIS_PREV_HASH, compute_event_id

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples"
SPEC_DIR = REPO_ROOT / "spec"


def _make_actor() -> dict[str, Any]:
    return {
        "type": "agent",
        "id": "test-agent@v0.0.1",
        "session": "test-session-1",
    }


def build_event(
    *,
    seq: int,
    prev_hash: str,
    ledger_id: str = "test-ledger-001",
    timestamp: str = "2026-06-22T12:00:00.000Z",
    event_type: str = "session.start",
    payload: dict[str, Any] | None = None,
    actor: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "ledger_id": ledger_id,
        "seq": seq,
        "timestamp": timestamp,
        "actor": actor or _make_actor(),
        "event_type": event_type,
        "payload": payload if payload is not None else {"k": "v"},
        "prev_hash": prev_hash,
    }
    event["event_id"] = compute_event_id(event)
    return event


@pytest.fixture
def make_event():
    return build_event


@pytest.fixture
def valid_chain() -> list[dict[str, Any]]:
    """build a 3-event valid chain on the fly."""
    e0 = build_event(seq=0, prev_hash=GENESIS_PREV_HASH, event_type="session.start")
    e1 = build_event(
        seq=1,
        prev_hash=e0["event_id"],
        event_type="tool.call.completed",
        payload={"tool": "echo", "latency_ms": 1},
        timestamp="2026-06-22T12:00:01.000Z",
    )
    e2 = build_event(
        seq=2,
        prev_hash=e1["event_id"],
        event_type="session.end",
        payload={"reason": "ok"},
        timestamp="2026-06-22T12:00:02.000Z",
    )
    return [e0, e1, e2]


@pytest.fixture
def examples_dir() -> Path:
    return EXAMPLES_DIR


@pytest.fixture
def clone():
    """deep-clone helper, since tests mutate events to introduce bugs."""
    return copy.deepcopy
