# SMAA 1.1 — Intervention and Recovery Extension

## New software capabilities

### Snapshot restoration
A verified snapshot can reconstruct the self-model only when its ledger-head digest matches a separately supplied trusted head. The restored engine starts a new local event ledger and records the snapshot ID, digest, prior trusted head, and restored model version. It does not pretend to restore or authenticate the old ledger. This is a model-state recovery path, not a distributed rollback/consensus protocol.

### Randomized intervention utilities
The experiment module supplies deterministic balanced random assignment and a two-arm Welch difference-in-means estimator with a normal-approximation 95% interval. It does not generate outcomes, randomize a real-world system, hide labels, or establish causality by itself. The experiment controller must keep allocation concealment, treatment delivery, outcome measurement, and analysis independent from the cells being evaluated.

## Preregistered functional self-model evaluation

Compare four variants under identical resource budgets:
- log-only memory;
- fixed self-report;
- explicit state tracker;
- active SMAA.

For each held-out environment, preregister randomized interventions: cell removal, identity replacement, capability removal, event delay/drop, resource perturbation, misleading actor metadata, counterexample injection, and restoration from a known snapshot. Include sham and no-intervention conditions. Keep treatment allocation and hidden outcomes inaccessible to cells and the orchestrator. Report treatment effect, uncertainty interval, calibration, false self-attribution, selective risk/coverage, revision/rollback quality, and total compute/communication/evaluator cost.

At least 20 independent seeds are a preliminary minimum, not a universal sample-size guarantee. Confirmatory sample sizes require power analysis. Do not tune on sealed outcomes.

## Interpretation boundary

A positive result supports only improved performance on the specified functional self-model tasks. It does not establish subjective experience, phenomenal consciousness, human-like awareness, or AGI. Software unit tests validate implementation behavior, not the scientific hypothesis.
