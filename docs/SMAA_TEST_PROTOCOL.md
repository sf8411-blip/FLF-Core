# SMAA 0.1.0 — Test Protocol

## Software acceptance tests
Run the unit suite on supported Python versions. It checks membership continuity, private-field rejection, message allow-listing, event tamper detection, self-model-dependent action gating, prediction scoring, social provenance, revision, and process-isolated summaries.

## Scientific evaluation (not yet run)
Compare under equal compute, memory and communication budgets:
A. event-log-only baseline;
B. fixed self-report baseline;
C. deterministic state tracker;
D. active self-model that changes decisions.

Interventions: remove, corrupt, delay, or replace self-model components; add/remove cells; swap cell identities; alter capability evidence; inject misleading actor labels. Use hidden held-out environments and preregister metrics before testing.

Metrics: identity reconstruction accuracy, false self-attribution, missed self-actions, calibration (Brier/ECE), abstention quality, revision precision/recall, task performance, latency, memory, communication and total compute.

A passing unit suite establishes software behavior only. It does not establish that the self-model improves task performance or that the network is conscious.
