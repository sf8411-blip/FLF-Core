# SMAA 1.2.1 — Blinded Experimental Harness

## Status
Adds seeded stratified allocation, a preregistration record and SHA-256 digest, spawned-process agent decisions, parent-process evaluator scoring, timeout enforcement, and JSONL records. This is a pilot harness, not a completed confirmatory experiment.

## Reproducibility
Register study ID, primary endpoint and direction, allocation seed, timeout, arms, and analysis-plan version before running. Allocation is independently shuffled within each stratum; arm counts differ by at most one. Every record includes the trial seed, stratum, arm, metrics, budget report, elapsed time, and preregistration digest. Preserve the exact code revision and trial manifest externally.

## Information boundary
The child process receives only the agent, its observation, and abstract budget limits. EvaluationTarget stays in the parent and is scored only after the child returns. Python spawn and a pipe provide process separation, not a hardened sandbox. For stronger isolation, configure OS/container controls: no network, read-only code, restricted filesystem, and resource limits.

## Limitations
No independent hidden generator, power analysis, inferential statistics, CPU-time or peak-memory accounting, or secure adversarial isolation is included. Abstract units do not establish equal physical compute. Results cannot establish consciousness, AGI, or general self-awareness.
