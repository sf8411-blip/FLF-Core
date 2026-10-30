"""SMAA: auditable functional self-modeling for digital-cell networks."""
from .core import (
    Capability, CellRecord, EventLedger, IsolatedCellProcess, KnowledgeClaim,
    SQLiteEventLedger, Prediction, SMAAEngine, brier_score,
    expected_calibration_error, normalized_prediction_error,
)
from .complete import (
    AgencyObservation, ModelSnapshot, RevisionDecision, RevisionGate,
    RevisionProposal, SMAAComplete, SQLiteSnapshotStore, estimate_agency,
)
__all__ = [
    "Capability", "CellRecord", "EventLedger", "IsolatedCellProcess",
    "KnowledgeClaim", "SQLiteEventLedger", "Prediction", "SMAAEngine",
    "brier_score", "expected_calibration_error", "normalized_prediction_error",
    "AgencyObservation", "ModelSnapshot", "RevisionDecision", "RevisionGate",
    "RevisionProposal", "SMAAComplete", "SQLiteSnapshotStore", "estimate_agency",
]
