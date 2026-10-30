from __future__ import annotations

import json

from .core import Capability, CellRecord, KnowledgeClaim, NetworkSelfModel, SMAAEngine
from .complete import ModelSnapshot


def restore_engine_from_snapshot(snapshot: ModelSnapshot, trusted_ledger_head: str) -> SMAAEngine:
    """Restore model state only after digest and externally trusted ledger-head checks.

    The old event ledger is not silently recreated. A new ledger records the restore
    operation and references the verified snapshot and trusted prior head.
    """
    if not snapshot.verify():
        raise ValueError("snapshot integrity verification failed")
    if not trusted_ledger_head or snapshot.ledger_head != trusted_ledger_head:
        raise ValueError("snapshot does not match the externally trusted ledger head")
    state = json.loads(snapshot.state_json)
    required = {"network_id", "version", "tick", "cells", "capabilities", "claims",
                "unknowns", "resources", "assumptions", "last_revision_reason"}
    if set(state) != required:
        raise ValueError("snapshot state schema mismatch")
    engine = SMAAEngine(snapshot.network_id)
    model = NetworkSelfModel(
        network_id=state["network_id"],
        version=state["version"],
        tick=state["tick"],
        cells={
            key: CellRecord(
                cell_id=value["cell_id"], joined_at=value["joined_at"],
                active=value["active"], capabilities=tuple(value["capabilities"])
            ) for key, value in state["cells"].items()
        },
        capabilities={
            key: Capability(
                name=value["name"], success_rate=value["success_rate"],
                trials=value["trials"], evidence_ids=tuple(value["evidence_ids"]),
                limitations=tuple(value["limitations"])
            ) for key, value in state["capabilities"].items()
        },
        claims={
            key: KnowledgeClaim(
                claim_id=value["claim_id"], proposition=value["proposition"],
                owner_cell_id=value["owner_cell_id"],
                evidence_ids=tuple(value["evidence_ids"]),
                independently_verified=value["independently_verified"]
            ) for key, value in state["claims"].items()
        },
        unknowns=list(state["unknowns"]),
        resources=dict(state["resources"]),
        assumptions=list(state["assumptions"]),
        last_revision_reason=state["last_revision_reason"],
    )
    if model.network_id != snapshot.network_id or model.version != snapshot.model_version:
        raise ValueError("restored model identity/version mismatch")
    if any(claim.owner_cell_id not in model.cells for claim in model.claims.values()):
        raise ValueError("snapshot contains a claim with an unknown owner")
    engine.model = model
    engine._record("model_restored_from_snapshot", "recovery", {
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_digest": snapshot.digest,
        "trusted_previous_ledger_head": trusted_ledger_head,
        "restored_model_version": model.version,
    })
    return engine
