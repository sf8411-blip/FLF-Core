# FLF-Core

Core repository for the digital-cell / decentralized learning research program.

## SMAA 1.0 — complete functional self-model reference

The smaa package provides network identity, cell lifecycle, capability and limitation evidence, prediction calibration, knowledge provenance, intervention-based agency bookkeeping, durable event history, integrity-checked model snapshots, and evidence-gated self-revision.

SMAA is a vertical subsystem spanning the seven functional layers; it is not an eighth layer. It is not a claim of phenomenal consciousness, sentience, or AGI.

### Run tests
```bash
python -m unittest discover -s tests -v
```

### Design and evaluation
- [SMAA architecture](docs/SMAA_ARCHITECTURE.md)
- [SMAA verification protocol](docs/SMAA_TEST_PROTOCOL.md)

The reference implementation is not yet integrated into a production GDC engine. Process isolation is not a hardened sandbox, and causal/revision components require blinded external evaluation before scientific claims are made.


## SMAA 1.1 — intervention and recovery extension

SMAA 1.1 adds verified self-model restoration from a snapshot only when its ledger-head reference matches an externally trusted head, plus reproducible balanced random assignment and a two-arm treatment-effect estimator for controlled evaluations.

- [SMAA 1.1 evaluation protocol](docs/SMAA_1_1_EVALUATION.md)
- Recovery does not restore or authenticate the historical event ledger; it starts a new ledger and records the verified snapshot provenance.
- Randomization and effect estimation are utilities, not a blinded experiment harness or proof of causality.
