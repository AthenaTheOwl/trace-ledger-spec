# A hash chain needs an independently retained anchor

The validator detects an edited payload whose event hash was left unchanged, a
broken predecessor link, an invalid event type, and a sequence gap. Those are
useful conformance properties. They do not establish that a ledger includes every
real action or that the actor writing a payload told the truth.

An operator able to replace an entire ledger can also recompute its hashes.
A consumer checking only the replacement file has no earlier head to compare.
Likewise, a shortened prefix can be internally consistent unless the consumer
knows a later head was previously observed. These limits follow from the local
hash-chain construction; this repository does not ship an external witness or
signed checkpoint service.

For a review handoff, retain the expected head digest, sequence count, schema and
vocabulary version outside the producer's write scope. Record who observed the
head and when. Validate the file locally, then compare its terminal digest with
the independently retained value. A notary receipt can bind a checkpoint manifest
to a signing identity, subject to that verifier's key assumptions; it still does
not establish that every external action was logged.

Separate four review questions: is the chain internally consistent, does it match
the observed checkpoint, are its payload claims supported by external evidence,
and does that evidence cover the current implementation? The validator answers
only the first. An agent's conclusion
should not stand in for the raw ledger and checkpoint in the review input.

Try a controlled exercise with a copy of the committed clean example. Retain its
head externally, alter a payload and recompute the whole chain in a separate
experimental copy, then compare the retained head. The external comparison should
reject the replacement even if local validation passes. This is an integration
exercise, not an additional conformance rule or schema revision.

No spec file, vocabulary, version or migration row changes with this note.
