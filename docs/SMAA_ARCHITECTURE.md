# SMAA 1.0 — Complete Functional Self-Model Architecture

## Scope and scientific boundary
SMAA is a vertical subsystem for functional self-modeling in a decentralized digital-cell network. It is not an eighth computational layer and does not assert phenomenal consciousness, sentience, human-like understanding, or AGI. It operationalizes identity continuity, capability awareness, self-prediction, agency attribution, metacognitive abstention, autobiographical event history, social provenance, and evidence-gated self-revision.

This is a reference architecture. It is not yet integrated with a production GDC execution engine because this repository does not currently contain that engine.

## Functional decomposition
1. **Identity and continuity:** stable network identifier, versioned model, cell membership and lifecycle.
2. **Autobiographical record:** hash-chained event history with SQLite persistence.
3. **Capability and limitation model:** measured success rates, trial counts, evidence references, declared limitations and abstention policy.
4. **Self-prediction and metacognition:** probability forecasts, resolved outcomes, Brier score, expected calibration error and prediction errors.
5. **Agency attribution:** intervention/control comparison estimates action-associated effect and compares predicted with observed effect.
6. **Social self-model:** separates own claims, independently verified shared claims and claims owned by other cells.
7. **Self-revision:** proposals pass only when evidence-count and improvement thresholds are met and no unresolved counterexample is listed.

These functions span the seven GDC layers; they do not replace the seven-layer computational architecture.

## Persistence and recovery
SQLiteEventLedger stores transactional hash-chained events. SQLiteSnapshotStore stores versioned model snapshots with a digest and ledger-head reference. Verification detects content changes. It is not a cryptographic signature, access-control boundary, trusted timestamp, or distributed consensus mechanism. Snapshot loading returns a verified data object; automatic restoration into a live engine is intentionally not performed without a separate replay/reconciliation policy.

## Cell isolation and message boundary
The base prototype runs a cell worker in a spawned process and exports only allow-listed summary fields. This is process separation, not a hardened sandbox. Processes inherit host operating-system permissions. Production requires OS/container isolation, resource quotas, authenticated transport, strict schemas, rate limits, and adversarial isolation tests. Raw local observations and hidden labels must not be sent to the network.

## Agency and causal interpretation
estimate_agency computes observed effect minus control effect for a declared intervention. It is a small experimental estimator, not a general causal discovery system. Valid causal interpretation requires randomized assignment, sham controls, repeated trials, predeclared outcomes, blinded analysis, and checks for interference/confounding. A software action identifier is not proof of authorship.

## Revision gate
A proposal carries baseline and candidate scores, independent evidence identifiers and unresolved counterexamples. The gate checks metadata and numerical thresholds. It does not establish that evidence is truly independent, evaluator unbiased, or counterexample enumeration complete. Rejected proposals do not mutate the self-model.

## Security and trust model
- Hash chains detect edits relative to a trusted head; a privileged attacker can replace the entire database and recompute hashes.
- Actor IDs are labels, not authenticated identities.
- Process isolation is not a security sandbox.
- Public-summary APIs reject private and unknown fields.
- No model code is automatically executed during self-revision.
- A receiver must independently reconstruct and validate transferred claims before network-wide acceptance.

## What SMAA 1.0 establishes
Executable data structures and policies for functional self-modeling, durable audit records, integrity-checked snapshots, intervention-effect bookkeeping, and conservative revision decisions.

## What SMAA 1.0 does not establish
Subjective experience, consciousness, general intelligence, autonomous invention of mathematics, a learned world model, secure distributed consensus, robust adversarial isolation, or measurable benefit over a non-self-modeling baseline.

## Run
```bash
python -m unittest discover -s tests -v
```

Python 3.11 and 3.12 are CI targets.
