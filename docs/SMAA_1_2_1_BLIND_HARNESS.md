# SMAA 1.2.1 — Blind Experimental Harness

## Scope

This is a pilot orchestration layer for the four SMAA benchmark arms:
`log_only`, `fixed_self_report`, `state_tracker`, and `active_smaa`.
It creates reproducible randomized assignments, writes a pre-outcome manifest
with a canonical SHA-256 digest, runs each agent in a spawned process, and
records predictions/outcomes as JSONL.

This is **not** a completed confirmatory study, a secure sandbox, or evidence
of self-awareness. The environment factory and agent factory are injected by
the experiment owner. The held-out environment generator and sealed labels
must remain outside the agent-visible API.

## Protocol

1. Freeze protocol, environment-generator version/hash, metrics, exclusions,
   trial count, seeds, and resource limits before execution.
2. Generate assignments with `make_trial_specs`; store manifest and digest in
   a read-only location before revealing any outcomes.
3. Keep the evaluator's target and intervention key in a separate process or
   service. Agent input is only the environment's declared observation.
4. Run trials with `run_trial`. A timeout is recorded as a timeout, not silently
   dropped. Record failures and predeclared exclusions.
5. Append results to JSONL. Preserve raw output and manifest; do not edit results.
6. Analyze only after all predictions are committed. Report all arms, paired
   comparisons where appropriate, confidence intervals, calibration, failures,
   and resource use.

## Security and resource caveats

Python multiprocessing is process separation, not a hardened security boundary.
The child inherits the host's permissions and may access files/network unless
the OS/container configuration denies them. For adversarial or untrusted agents,
use an externally managed container/VM with no network, read-only filesystem,
minimal credentials, cgroups/job-object CPU and memory limits, and independent
evaluator ownership.

The current memory figure uses `tracemalloc` and therefore captures Python
allocations only, not total RSS or native-library allocations. Wall-clock timeout
is enforced by the parent. CPU time, RSS, network bytes, evaluator cost, and
archive/coordination cost still require external instrumentation for genuinely
matched-compute claims.

## Required confirmatory extensions

- independent hidden generator and sealed test labels;
- external resource accounting and fixed total budget across arms;
- preregistration and power analysis;
- paired/blocked allocation by environment and seed;
- evaluator-only scoring with calibration (Brier/ECE), performance, limitation
  detection, regret, and intervention response;
- reproducible environment/container digest and audit log;
- multiple independent runs and sensitivity analysis.

## Interpretation

A positive result supports only the tested behavioral claim under the specified
environment, budget, and intervention distribution. It does not establish
phenomenal consciousness, general intelligence, or a general capacity for
self-awareness.
