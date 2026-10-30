# SMAA 0.1.0 — Self-Model & Awareness Architecture

## Purpose and boundary
SMAA is a functional self-modeling subsystem for a digital-cell network. It is not an eighth computational layer and does not assert phenomenal consciousness. It is a vertical capability spanning observation, representation, hypothesis, validation, diversity, communication and collective verification.

## Model contents
- Persistent network identifier and versioned self-model.
- Membership state: active/inactive cells and join history.
- Capability ledger: measured success rate, trial count, evidence references and limitations.
- Knowledge provenance: claim owner, evidence references and independent-verification flag.
- Internal status: bounded resource summaries and declared unknowns.
- Metacognition: forecasts, resolved outcomes, Brier score and expected calibration error.
- Agency provenance: events include actor labels and event type.
- Self-revision: reasoned model-version increments and explicit assumptions.

## Information boundary
The reference provides a spawned process per cell. A child process retains observations and exports only an allow-listed summary. This is process separation, not a hardened sandbox: workers still run with the host user's permissions. Production deployment needs OS/container isolation, authenticated transport, schema validation, quotas and adversarial tests. The parent API independently rejects unknown and private message fields.

## Audit limitations
The SHA-256 event chain detects edits relative to a trusted chain head. It does not authenticate actors, prevent complete history replacement, or provide distributed consensus. Actor identifiers are assertions until cryptographically bound to process identities.

## Functional self-model versus consciousness
A working self-model can support identity tracking, action attribution, capability awareness, calibrated prediction and revision. Passing software tests does not demonstrate subjective experience, human-like consciousness, or general intelligence.

## Completion status
- Implemented: schemas, network state, membership, capability evidence, public message allow-list, hash-chained event ledger, claim provenance, attempt/abstain policy, prediction scoring and versioned revision.
- Partial: per-cell process isolation and event history (no hardened sandbox or durable persistence).
- Not implemented: learned world/self predictive model, causal agency experiments, cryptographic identity, rollback of arbitrary code, autonomous grammar invention, and integration with the GDC experimental engine.
