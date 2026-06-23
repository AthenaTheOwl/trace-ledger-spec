"""trace-ledger-spec — live demo (Streamlit Community Cloud).

Mirrors the no-arg `report` verb: validates every committed example ledger
under examples/*.jsonl against the spec (schema + controlled vocab + hash
chain) and shows pass/fail per file plus the rule that caught each planted
bug. You can also paste or upload your own ledger to validate it live.

No network, no secrets — runs entirely off the committed examples and the
in-repo reference validator.

Deploy: Streamlit Community Cloud -> New app -> repo AthenaTheOwl/trace-ledger-spec,
branch main, main file streamlit_app.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from trace_ledger_spec.validator import (
    GENESIS_PREV_HASH,
    compute_event_id,
    load_vocab,
    read_jsonl,
    validate_event,
    validate_ledger,
)

REPO = Path(__file__).resolve().parent
EXAMPLES = REPO / "examples"

# what each shipped example proves, and the rule the negative cases trip.
BLURB = {
    "valid.jsonl": "clean 5-event ledger; satisfies every spec rule",
    "bad_event_type.jsonl": "event_type off the controlled vocabulary",
    "seq_gap.jsonl": "seq jumps 1->3, breaking the prev_hash chain",
    "tampered_hash.jsonl": "payload altered; event_id no longer matches its bytes",
}
NEGATIVE = ("bad_event_type.jsonl", "seq_gap.jsonl", "tampered_hash.jsonl")
RULE = {"bad_event_type.jsonl": "vocab", "seq_gap.jsonl": "chain", "tampered_hash.jsonl": "hash"}


def first_error(result) -> str:
    """short, path-free summary of the first error a ledger tripped."""
    if not result.errors:
        return ""
    msg = result.errors[0]
    if msg.startswith("event ") and ": " in msg:
        msg = msg.split(": ", 1)[1]
    for r in ("vocab: ", "chain: ", "hash: "):
        if msg.startswith(r):
            msg = msg[len(r):]
            break
    if msg.startswith("event_id mismatch"):
        msg = "event_id mismatch (recomputed hash differs)"
    return msg


st.set_page_config(page_title="trace-ledger-spec — reference validator", layout="wide")
st.title("trace-ledger-spec")
st.caption(
    "reference validator for an append-only agent trace ledger: it runs the "
    "committed example ledgers through the spec (json schema + controlled vocab "
    "+ content-addressable hash chain) and shows what each rule catches."
)

paths = sorted(EXAMPLES.glob("*.jsonl"))
if not paths:
    st.warning("no example ledgers found under examples/*.jsonl")
    st.stop()

# clean control first, then planted-bug ledgers (mirrors the report verb).
paths.sort(key=lambda p: (p.name in NEGATIVE, p.name))

rows = []
n_pass = n_fail = expected_ok = 0
expected_ok = True
for path in paths:
    name = path.name
    try:
        events = read_jsonl(path)
    except (FileNotFoundError, ValueError) as exc:
        rows.append({"ledger": name, "events": 0, "verdict": "ERROR",
                     "what it exercises": str(exc), "caught by": ""})
        expected_ok = False
        continue
    result = validate_ledger(events)
    is_neg = name in NEGATIVE
    verdict = "PASS" if result.ok else "FAIL"
    if result.ok == is_neg:
        expected_ok = False
    if result.ok:
        n_pass += 1
    else:
        n_fail += 1
    caught = "" if result.ok else first_error(result)
    rule = RULE.get(name, "")
    rows.append({
        "ledger": name,
        "events": len(events),
        "verdict": verdict,
        "what it exercises": BLURB.get(name, ""),
        "caught by": f"{rule}: {caught}" if rule and caught else caught,
    })

c1, c2, c3 = st.columns(3)
c1.metric("example ledgers", len(rows))
c2.metric("clean (pass)", n_pass)
c3.metric("planted bugs caught", n_fail, help="off-vocabulary type, seq gap, tampered payload")

view = st.selectbox("show", ["all ledgers", "only passing", "only failing"], index=0)
shown = rows
if view == "only passing":
    shown = [r for r in rows if r["verdict"] == "PASS"]
elif view == "only failing":
    shown = [r for r in rows if r["verdict"] != "PASS"]

st.dataframe(shown, use_container_width=True, hide_index=True)

if expected_ok:
    st.success(
        f"key finding: {n_pass} clean ledger passed and {n_fail} planted-bug ledgers "
        f"were caught by the exact rule each was designed to trip "
        f"(vocab / chain / hash). all examples behaved as designed."
    )
else:
    st.warning("an example did not behave as designed — the committed fixtures may have drifted.")

with st.expander("the spec rules the validator enforces"):
    st.markdown(
        "- each event matches the json schema (`spec/trace-event.schema.json`).\n"
        "- `event_type` is drawn from the controlled vocab (`spec/event-types.yaml`).\n"
        "- `event_id` == sha256 of canonical-json of the event minus `event_id` "
        "(sorted keys, no whitespace, utf-8).\n"
        "- across a ledger: `ledger_id` constant; `seq` starts at 0 and increments "
        "by 1 with no gaps; `prev_hash[n] == event_id[n-1]`, genesis prev_hash is sha256:0...0."
    )

st.divider()
st.subheader("build an event and watch the validator")
st.caption(
    "set the fields of a single genesis event; the page runs the real "
    "`validate_event` (json schema + controlled vocab + self-hash) live as you "
    "change them. flip a field off-spec to see exactly which rule trips, then "
    "seal it with the real `compute_event_id` hash function."
)

vocab_names, vocab_version = load_vocab()
vocab_sorted = sorted(vocab_names)

b1, b2 = st.columns(2)
with b1:
    ledger_id = st.text_input("ledger_id", value="01HZTRACELEDGERDEMO01")
    seq = st.number_input("seq", min_value=0, value=0, step=1)
    timestamp = st.text_input("timestamp (rfc3339 utc)", value="2026-06-22T10:00:00.000Z")
    use_real_type = st.checkbox(
        "use an event_type from the controlled vocab", value=True,
        help=f"vocab v{vocab_version}: {len(vocab_sorted)} allowed types",
    )
    if use_real_type:
        event_type = st.selectbox("event_type", vocab_sorted, index=vocab_sorted.index("session.start"))
    else:
        event_type = st.text_input("event_type (off-vocab)", value="made.up.type")
with b2:
    actor_type = st.selectbox("actor.type", ["agent", "human", "system", "tool"], index=0)
    actor_id = st.text_input("actor.id", value="demo-agent@v0.1.0")
    payload_text = st.text_area("payload (json object)", value='{"session_id": "demo-1"}', height=90)
    prev_hash = st.text_input(
        "prev_hash", value=GENESIS_PREV_HASH,
        help="genesis is sha256 + 64 zeros; for a non-genesis event this is the previous event_id",
    )

payload_ok = True
try:
    payload = json.loads(payload_text) if payload_text.strip() else {}
    if not isinstance(payload, dict):
        payload_ok = False
        st.error("payload must be a json object")
except json.JSONDecodeError as exc:
    payload_ok = False
    st.error(f"payload is not valid json: {exc}")
    payload = {}

if payload_ok:
    # build the event WITHOUT event_id, then seal it with the real hash engine.
    body = {
        "ledger_id": ledger_id,
        "seq": int(seq),
        "timestamp": timestamp,
        "actor": {"type": actor_type, "id": actor_id},
        "event_type": event_type,
        "payload": payload,
        "prev_hash": prev_hash,
    }
    sealed_id = compute_event_id(body)  # real engine: content-addressable hash

    seal = st.radio(
        "event_id",
        ["seal with the real hash (compute_event_id)", "set a wrong hash on purpose"],
        index=0, horizontal=True,
    )
    event_id = sealed_id if seal.startswith("seal") else "sha256:" + ("0" * 63 + "1")
    event = {"event_id": event_id, **body}

    st.code(json.dumps(event, indent=2, sort_keys=True), language="json")

    # real engine call: single-event validation (schema + vocab + self-hash).
    result = validate_event(event, vocab=vocab_names)
    if result.ok:
        st.success("PASS — schema, controlled vocab, and self-hash all satisfied.")
    else:
        st.error(f"FAIL — {len(result.errors)} rule(s) tripped:")
        for err in result.errors:
            st.markdown(f"- `{err}`")
    st.caption(f"real event_id for these bytes: `{sealed_id}`")

st.divider()
st.subheader("validate your own ledger")
st.caption("paste jsonl (one event per line) or upload a .jsonl file; it runs through the same validator.")

uploaded = st.file_uploader("upload a .jsonl ledger", type=["jsonl"])
default_text = (EXAMPLES / "valid.jsonl").read_text(encoding="utf-8")
pasted = st.text_area("…or paste jsonl here", value=default_text, height=160)

raw = ""
if uploaded is not None:
    raw = uploaded.getvalue().decode("utf-8")
elif pasted.strip():
    raw = pasted

if raw.strip():
    try:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    except json.JSONDecodeError as exc:
        st.error(f"invalid json: {exc}")
    else:
        result = validate_ledger(events)
        if result.ok:
            st.success(f"PASS — {len(events)} events, every spec rule satisfied.")
        else:
            st.error(f"FAIL — {len(result.errors)} error(s):")
            for err in result.errors:
                st.markdown(f"- `{err}`")

st.caption(
    "this page reads the committed `examples/*.jsonl` and runs the in-repo "
    "`trace_ledger_spec.validator`. repo: github.com/AthenaTheOwl/trace-ledger-spec"
)
