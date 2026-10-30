# SMAA 1.2 — Empirical Self-Modeling Benchmark

## Status

This change adds benchmark interfaces, four reference control architectures, behavioral scoring, and abstract per-component budget accounting. It does **not** claim that a confirmatory hidden-environment study has been run.

## Four arms

1. **Log-only** — records current input but does not build an active self-model.
2. **Fixed self-report** — uses a static, predeclared self-description.
3. **State tracker** — maps currently observed state into predictions without prediction-error-driven revision.
4. **Active SMAA** — maintains a minimal predictive self-model and updates its performance bias from post-trial feedback.

All arms use the same observation schema and are scored by the same evaluator interface. Ground-truth targets are represented by a separate evaluator-only type and are not passed to agent decision methods.

## Primary behavioral outcomes

- **Self-behavior prediction:** mean absolute error between predicted and realized performance.
- **Limitation detection:** accuracy of predicting whether a required capability is available; report sensitivity, specificity, and balanced accuracy in confirmatory analysis.
- **Identity recognition:** exact-match accuracy against evaluator-only identity ground truth.
- **Decision quality:** mean reward and regret relative to the best available action in the sealed target.

Secondary outcome: **confidence calibration**, measured by Brier score for capability-availability confidence. A confirmatory study should also report reliability diagrams and ECE with preregistered binning.

Natural-language self-reports are not a success metric.

## Budget accounting

BudgetLimits assigns equal per-trial ceilings to environment, agent, evaluator, communication, and archive components. BudgetMeter enforces each ceiling and records actual usage. The reference agents consume different abstract agent-compute units (1/2/3/5); this supports cost-performance analysis but is not strict equal-compute matching. A confirmatory study must compare performance at matched cumulative agent compute or use a common fixed allotment. Record wall-clock CPU time, peak memory, bytes transmitted, evaluator cost, and archive cost in the external controller. Abstract units are not physical compute measurements.

## Blinding and leakage controls

- The evaluator must generate and retain sealed targets outside the agent process.
- Agent APIs receive AgentObservation; EvaluationTarget is passed only to the scorer.
- Do not place hidden labels, future outcomes, generator parameters, or target identity in observations, logs, exception messages, or shared storage.
- Run each arm in a separate process/container in the confirmatory harness. This module provides API-level separation, not a security sandbox.
- Use an independent held-out environment generator and sealed test set. Repository fixtures are software smoke tests, not hidden or confirmatory environments.
- The evaluator must not disclose outcome labels to agents until the preregistered feedback point. If feedback is supplied, disclose only the same allowed observation to every arm.

## Randomization and analysis

Use the SMAA 1.1 random assignment helper from an independent controller to allocate matched experimental units to arms. Stratify by environment family and intervention class. Preserve assignment seeds and allocation records outside agent-readable storage.

Preregister the primary endpoint and direction, randomization and analysis unit, power-based sample size, exclusion/missing-data rules, intervention schedule and sham controls, multiplicity correction, and paired or clustered uncertainty estimates where observations share environment seeds.

Twenty independent seeds are a pilot floor, not a universal sample-size guarantee. Confirmatory sample size must be justified by power analysis. Do not tune thresholds on sealed outcomes.

## Interpretation

A positive result supports only improved performance on the specified functional self-model tasks under tested conditions. It does not establish phenomenal consciousness, subjective experience, general intelligence, or AGI.

## Known limitations

- Reference agents are minimal and are not a complete production SMAA integration.
- Action policies are simple; independent environments must include nontrivial action utilities.
- The reference evaluator computes core metrics; sensitivity/specificity, confidence intervals, hierarchical models, and multiplicity adjustment belong in confirmatory analysis.
- Abstract budget units are accounting units, not CPU cycles or joules.
- No sealed environment generator is included by design.
