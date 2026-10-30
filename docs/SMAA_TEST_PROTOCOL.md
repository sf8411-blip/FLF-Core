# SMAA 1.0 — Verification and Scientific Evaluation Protocol

## A. Software acceptance
Run the complete suite on Python 3.11 and 3.12. Required checks include identity continuity, strict public-message allow-listing, event-chain and SQLite integrity, snapshot persistence and tamper detection, prediction scoring and abstention, claim provenance, intervention/control effect calculation, revision acceptance/rejection, and process-separated summaries.

A passing suite verifies specified software behavior only.

## B. Functional self-model experiment
Compare under identical compute, memory, and communication budgets:
1. **Log-only:** event history, no explicit self-model.
2. **Fixed self-report:** static self-description, not updated from outcomes.
3. **State tracker:** explicit identity and capability state, no predictive feedback.
4. **Active SMAA:** predicts own behavior, compares prediction with outcome, and revises through the evidence gate.

Use a hidden environment generator unavailable to implementation authors. Preregister seeds, sample size, outcomes, exclusions, analysis, and stopping rules. Use paired seeds and at least 20 independent seeds for an initial study; power analysis is required for confirmatory claims.

## C. Intervention matrix
Randomly assign and repeat: remove a cell; replace a cell identity while preserving observations; remove/corrupt a capability record; delay/suppress an event; inject a misleading actor label; alter resource availability; introduce a counterexample to an accepted self-claim; restore a prior verified snapshot. Include sham and no-intervention controls. Keep hidden labels inaccessible to cells and orchestration code.

## D. Primary metrics
Identity reconstruction and continuity errors; false/missed self-attribution; Brier score and expected calibration error; selective risk/coverage for attempt-versus-abstain; revision precision, recall and rollback rate; held-out task performance; latency, memory, messages, evaluator cost and total compute.

## E. Causal agency evaluation
Randomize action assignment where possible. Estimate treatment effect as the difference between action and control outcomes. Repeat across contexts and test prediction transfer to unseen contexts. Do not infer agency from correlation or self-report alone.

## F. Acceptance criteria
Before data collection, define thresholds for meaningful improvement over all three controls, no unacceptable increase in false attribution, calibrated confidence, reproducible revision decisions, and complete accounting of total system cost. Do not tune on sealed tests. Report confidence intervals and negative results.

## G. Interpretation
Success supports only the claim that the active architecture improves specified functional self-model tasks under tested conditions. It does not establish phenomenal consciousness, human-like awareness, or AGI.
