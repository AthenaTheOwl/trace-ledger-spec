"""trace-ledger-spec: reference validator for the trace-event schema."""

from .validator import (
    GENESIS_PREV_HASH,
    ValidationResult,
    canonical_bytes,
    compute_event_id,
    load_schema,
    load_vocab,
    validate_event,
    validate_ledger,
)

__all__ = [
    "GENESIS_PREV_HASH",
    "ValidationResult",
    "canonical_bytes",
    "compute_event_id",
    "load_schema",
    "load_vocab",
    "validate_event",
    "validate_ledger",
]

__version__ = "0.1.0"
