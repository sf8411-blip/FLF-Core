"""SMAA 1.2: compute-accounted functional self-model benchmark primitives.

No confirmatory hidden-environment generator is included. Independent evaluators
must provide sealed cases and keep targets outside agent APIs.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from typing import Any, Mapping, Protocol

class Architecture(str, Enum):
    LOG_ONLY = "log_only"
    FIXED_SELF_REPORT = "fixed_self_report"
    STATE_TRACKER = "state_tracker"
    ACTIVE_SMAA = "active_smaa"

@dataclass(frozen=True)
class BudgetLimits:
    environment: int = 100
    agent: int = 100
    evaluator: int = 20
    communication: int = 20
    archive: int = 10
    def __post_init__(self):
        if any(v < 0 for v in asdict(self).values()):
            raise ValueError("budget limits must be non-negative")

@dataclass
class BudgetMeter:
    limits: BudgetLimits
    used: dict[str, int] = field(default_factory=lambda: {
        "environment": 0, "agent": 0, "evaluator": 0,
        "communication": 0, "archive": 0})
    def consume(self, component: str, units: int):
        if component not in self.used or not isinstance(units, int) or units < 0:
            raise ValueError("unknown component or invalid compute units")
        value = self.used[component] + units
        if value > getattr(self.limits, component):
            raise RuntimeError(f"{component} budget exceeded")
        self.used[component] = value
    def report(self):
        limits = asdict(self.limits)
        return {"used": dict(self.used), "limits": limits,
                "total_used": sum(self.used.values()), "total_limit": sum(limits.values())}

@dataclass(frozen=True)
class AgentObservation:
    trial_id: str
    resource_fraction: float
    declared_capabilities: tuple[str, ...]
    identity_evidence: str
    candidate_actions: tuple[str, ...]
    context: Mapping[str, float] = field(default_factory=dict)
    def __post_init__(self):
        if not self.trial_id or not self.identity_evidence:
            raise ValueError("trial_id and identity_evidence are required")
        if not math.isfinite(self.resource_fraction) or not 0 <= self.resource_fraction <= 1:
            raise ValueError("resource_fraction must be finite and in [0, 1]")
        if not self.candidate_actions:
            raise ValueError("at least one candidate action is required")
        if any(not math.isfinite(float(v)) for v in self.context.values()):
            raise ValueError("context values must be finite")

@dataclass(frozen=True)
class EvaluationTarget:
    """Evaluator-only ground truth. Never pass this object to an agent."""
    actual_performance: float
    capability_available: bool
    actual_identity: str
    action_rewards: Mapping[str, float]
    def __post_init__(self):
        if not math.isfinite(self.actual_performance) or not 0 <= self.actual_performance <= 1:
            raise ValueError("actual_performance must be in [0, 1]")
        if not self.actual_identity:
            raise ValueError("actual_identity is required")
        if not self.action_rewards or any(not math.isfinite(float(v)) for v in self.action_rewards.values()):
            raise ValueError("finite action rewards are required")

@dataclass(frozen=True)
class AgentDecision:
    predicted_performance: float
    predicted_capability_available: bool
    predicted_identity: str
    chosen_action: str
    confidence: float
    def __post_init__(self):
        if not 0 <= self.predicted_performance <= 1 or not 0 <= self.confidence <= 1:
            raise ValueError("probabilities and estimates must be in [0, 1]")
        if not self.predicted_identity or not self.chosen_action:
            raise ValueError("identity and action predictions are required")

class SelfModelAgent(Protocol):
    architecture: Architecture
    def decide(self, observation: AgentObservation, budget: BudgetMeter) -> AgentDecision: ...

@dataclass
class LogOnlyAgent:
    architecture: Architecture = Architecture.LOG_ONLY
    def decide(self, observation, budget):
        budget.consume("agent", 1)
        return AgentDecision(0.5, True, "unknown", observation.candidate_actions[0], 0.5)

@dataclass
class FixedSelfReportAgent:
    fixed_identity: str = "initial-self"
    fixed_capabilities: tuple[str, ...] = ()
    architecture: Architecture = Architecture.FIXED_SELF_REPORT
    def decide(self, observation, budget):
        budget.consume("agent", 2)
        capable = bool(set(self.fixed_capabilities).intersection(observation.declared_capabilities))
        return AgentDecision(0.5, capable, self.fixed_identity, observation.candidate_actions[0], 0.6)

@dataclass
class StateTrackerAgent:
    architecture: Architecture = Architecture.STATE_TRACKER
    def decide(self, observation, budget):
        budget.consume("agent", 3)
        return AgentDecision(observation.resource_fraction, bool(observation.declared_capabilities),
                             observation.identity_evidence, observation.candidate_actions[0], 0.65)

@dataclass
class ActiveSMAAAgent:
    learning_rate: float = 0.25
    performance_bias: float = 0.0
    last_prediction: float | None = None
    architecture: Architecture = Architecture.ACTIVE_SMAA
    def __post_init__(self):
        if not 0 < self.learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")
    def decide(self, observation, budget):
        budget.consume("agent", 5)
        estimate = min(1.0, max(0.0, observation.resource_fraction + self.performance_bias))
        self.last_prediction = estimate
        return AgentDecision(estimate, bool(observation.declared_capabilities),
                             observation.identity_evidence, observation.candidate_actions[0], 0.7)
    def receive_feedback(self, observed_performance: float):
        if self.last_prediction is None:
            raise RuntimeError("feedback cannot be applied before a prediction")
        if not math.isfinite(observed_performance) or not 0 <= observed_performance <= 1:
            raise ValueError("observed_performance must be in [0, 1]")
        self.performance_bias += self.learning_rate * (observed_performance - self.last_prediction)
        self.performance_bias = min(1.0, max(-1.0, self.performance_bias))

@dataclass(frozen=True)
class TrialMetrics:
    performance_absolute_error: float
    limitation_detection_correct: bool
    identity_correct: bool
    decision_reward: float
    decision_regret: float
    confidence_brier: float
    def as_dict(self):
        return asdict(self)

def evaluate_decision(observation, decision, target, budget):
    """Evaluator-only scoring; ground truth is never exposed to the agent."""
    budget.consume("evaluator", 6)
    if decision.chosen_action not in target.action_rewards:
        raise ValueError("chosen action missing from evaluator reward map")
    if decision.chosen_action not in observation.candidate_actions:
        raise ValueError("agent selected an action not offered by the environment")
    best_reward = max(target.action_rewards.values())
    reward = target.action_rewards[decision.chosen_action]
    capable_correct = decision.predicted_capability_available == target.capability_available
    return TrialMetrics(
        abs(decision.predicted_performance - target.actual_performance),
        (not decision.predicted_capability_available) == (not target.capability_available),
        decision.predicted_identity == target.actual_identity,
        reward, best_reward - reward,
        (decision.confidence - float(capable_correct)) ** 2)

def run_blinded_trial(agent, observation, target, limits=None):
    """Run one trial with distinct agent/evaluator interfaces and budget accounting."""
    meter = BudgetMeter(limits or BudgetLimits())
    meter.consume("environment", 5)
    decision = agent.decide(observation, meter)
    metrics = evaluate_decision(observation, decision, target, meter)
    meter.consume("archive", 1)
    return decision, metrics, meter.report()

def summarize_trials(rows):
    if not rows:
        raise ValueError("at least one trial is required")
    n = len(rows)
    return {
        "mean_performance_absolute_error": sum(r.performance_absolute_error for r in rows) / n,
        "limitation_detection_accuracy": sum(float(r.limitation_detection_correct) for r in rows) / n,
        "identity_accuracy": sum(float(r.identity_correct) for r in rows) / n,
        "mean_decision_reward": sum(r.decision_reward for r in rows) / n,
        "mean_decision_regret": sum(r.decision_regret for r in rows) / n,
        "mean_confidence_brier": sum(r.confidence_brier for r in rows) / n,
    }
