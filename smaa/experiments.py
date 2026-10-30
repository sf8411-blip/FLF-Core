from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class RandomizedAssignment:
    assignments: dict[str, bool]
    seed: int


@dataclass(frozen=True)
class TreatmentEffectEstimate:
    treatment_n: int
    control_n: int
    treatment_mean: float
    control_mean: float
    difference_in_means: float
    standard_error: float
    ci95_low: float
    ci95_high: float


def randomize_units(unit_ids: Sequence[str], seed: int) -> RandomizedAssignment:
    """Create a reproducible, approximately balanced treatment allocation."""
    ids = list(unit_ids)
    if len(ids) < 4 or len(set(ids)) != len(ids) or any(not x for x in ids):
        raise ValueError("at least four unique, non-empty unit IDs are required")
    rng = random.Random(seed)
    shuffled = ids[:]
    rng.shuffle(shuffled)
    treated = set(shuffled[:len(ids) // 2])
    return RandomizedAssignment({unit: unit in treated for unit in ids}, seed)


def estimate_randomized_effect(
    outcomes: Mapping[str, float],
    assignments: Mapping[str, bool],
) -> TreatmentEffectEstimate:
    """Welch difference-in-means estimate for a randomized two-arm experiment."""
    if set(outcomes) != set(assignments) or not outcomes:
        raise ValueError("outcome and assignment IDs must match exactly")
    if any(not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in outcomes.values()):
        raise ValueError("all outcomes must be finite numeric values")
    treatment = [float(outcomes[k]) for k, assigned in assignments.items() if assigned]
    control = [float(outcomes[k]) for k, assigned in assignments.items() if not assigned]
    if len(treatment) < 2 or len(control) < 2:
        raise ValueError("at least two units per arm are required")
    tm, cm = sum(treatment) / len(treatment), sum(control) / len(control)
    tv = sum((x - tm) ** 2 for x in treatment) / (len(treatment) - 1)
    cv = sum((x - cm) ** 2 for x in control) / (len(control) - 1)
    se = math.sqrt(tv / len(treatment) + cv / len(control))
    diff = tm - cm
    return TreatmentEffectEstimate(
        treatment_n=len(treatment), control_n=len(control),
        treatment_mean=tm, control_mean=cm, difference_in_means=diff,
        standard_error=se, ci95_low=diff - 1.96 * se, ci95_high=diff + 1.96 * se,
    )
