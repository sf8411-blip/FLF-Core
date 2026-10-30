"""SMAA: auditable functional self-modeling for digital-cell networks.

This package implements a testable software self-model. It makes no claim of
phenomenal consciousness or human-like subjective experience.
"""
from .core import (
    Capability, CellRecord, EventLedger, IsolatedCellProcess, KnowledgeClaim, SQLiteEventLedger,
    Prediction, SMAAEngine, brier_score, expected_calibration_error,
    normalized_prediction_error,
)
__all__ = [
    "Capability", "CellRecord", "EventLedger", "IsolatedCellProcess",
    "KnowledgeClaim", "SQLiteEventLedger", "Prediction", "SMAAEngine", "brier_score",
    "expected_calibration_error", "normalized_prediction_error",
]
