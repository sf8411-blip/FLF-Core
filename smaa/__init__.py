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
from .experiments import RandomizedAssignment, TreatmentEffectEstimate, estimate_randomized_effect, randomize_units
from .recovery import restore_engine_from_snapshot
from .benchmark import (
    ActiveSMAAAgent, AgentDecision, AgentObservation, Architecture, BudgetLimits,
    BudgetMeter, EvaluationTarget, FixedSelfReportAgent, LogOnlyAgent,
    StateTrackerAgent, TrialMetrics, evaluate_decision, run_blinded_trial,
    summarize_trials,
)
from .harness import (
    Preregistration, TrialRecord, TrialSpec, balanced_random_assignment,
    preregistration_digest, run_isolated_decision, run_study, write_jsonl,
)
__all__ = [
    "Capability", "CellRecord", "EventLedger", "IsolatedCellProcess",
    "KnowledgeClaim", "SQLiteEventLedger", "Prediction", "SMAAEngine",
    "brier_score", "expected_calibration_error", "normalized_prediction_error",
    "AgencyObservation", "ModelSnapshot", "RevisionDecision", "RevisionGate",
    "RevisionProposal", "SMAAComplete", "SQLiteSnapshotStore", "estimate_agency",
    "RandomizedAssignment", "TreatmentEffectEstimate", "estimate_randomized_effect",
    "randomize_units", "restore_engine_from_snapshot",
    "ActiveSMAAAgent", "AgentDecision", "AgentObservation", "Architecture",
    "BudgetLimits", "BudgetMeter", "EvaluationTarget", "FixedSelfReportAgent",
    "LogOnlyAgent", "StateTrackerAgent", "TrialMetrics", "evaluate_decision",
    "run_blinded_trial", "summarize_trials",
    "Preregistration", "TrialRecord", "TrialSpec", "balanced_random_assignment",
    "preregistration_digest", "run_isolated_decision", "run_study", "write_jsonl",
]
