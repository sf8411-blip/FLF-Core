from __future__ import annotations
import hashlib, json, sqlite3
from dataclasses import dataclass
from typing import Any

SNAPSHOT_SCHEMA_VERSION = 1

def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

@dataclass(frozen=True)
class ModelSnapshot:
    snapshot_id: str
    schema_version: int
    network_id: str
    model_version: int
    ledger_head: str
    state_json: str
    digest: str

    @classmethod
    def create(cls, snapshot_id: str, state: dict, ledger_head: str) -> "ModelSnapshot":
        if not snapshot_id or not ledger_head:
            raise ValueError("snapshot_id and ledger_head are required")
        network_id, version = state.get("network_id"), state.get("version")
        if not isinstance(network_id, str) or not network_id or not isinstance(version, int) or version < 1:
            raise ValueError("invalid self-model state")
        state_json = _canonical(state)
        body = {"snapshot_id": snapshot_id, "schema_version": SNAPSHOT_SCHEMA_VERSION,
                "network_id": network_id, "model_version": version,
                "ledger_head": ledger_head, "state_json": state_json}
        digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        return cls(snapshot_id, SNAPSHOT_SCHEMA_VERSION, network_id, version, ledger_head, state_json, digest)

    def verify(self) -> bool:
        body = {"snapshot_id": self.snapshot_id, "schema_version": self.schema_version,
                "network_id": self.network_id, "model_version": self.model_version,
                "ledger_head": self.ledger_head, "state_json": self.state_json}
        expected = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
        try:
            state = json.loads(self.state_json)
        except (TypeError, json.JSONDecodeError):
            return False
        return (self.schema_version == SNAPSHOT_SCHEMA_VERSION and
                state.get("network_id") == self.network_id and
                state.get("version") == self.model_version and expected == self.digest)

class SQLiteSnapshotStore:
    """Append-only snapshot records; integrity is detectable, not access-controlled."""
    def __init__(self, database_path: str):
        if not database_path:
            raise ValueError("database_path required")
        self.database_path = database_path
        with sqlite3.connect(database_path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS smaa_snapshots (
                snapshot_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL,
                network_id TEXT NOT NULL, model_version INTEGER NOT NULL,
                ledger_head TEXT NOT NULL, state_json TEXT NOT NULL, digest TEXT NOT NULL
            )""")
            db.commit()

    def save(self, snapshot: ModelSnapshot) -> None:
        if not snapshot.verify():
            raise ValueError("snapshot integrity check failed")
        with sqlite3.connect(self.database_path, timeout=10) as db:
            db.execute("INSERT INTO smaa_snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (snapshot.snapshot_id, snapshot.schema_version, snapshot.network_id,
                        snapshot.model_version, snapshot.ledger_head, snapshot.state_json, snapshot.digest))
            db.commit()

    def load(self, snapshot_id: str) -> ModelSnapshot:
        with sqlite3.connect(self.database_path) as db:
            row = db.execute("SELECT snapshot_id, schema_version, network_id, model_version, "
                             "ledger_head, state_json, digest FROM smaa_snapshots WHERE snapshot_id=?",
                             (snapshot_id,)).fetchone()
        if row is None:
            raise KeyError(snapshot_id)
        snapshot = ModelSnapshot(*row)
        if not snapshot.verify():
            raise ValueError("stored snapshot failed integrity verification")
        return snapshot

@dataclass(frozen=True)
class AgencyObservation:
    action_id: str
    predicted_effect: float
    observed_effect: float
    control_effect: float
    intervention_id: str
    def __post_init__(self):
        if not self.action_id or not self.intervention_id:
            raise ValueError("action and intervention identifiers are required")
        if any(not isinstance(v, (int, float)) for v in
               (self.predicted_effect, self.observed_effect, self.control_effect)):
            raise TypeError("effects must be numeric")

def estimate_agency(observation: AgencyObservation, tolerance: float = 0.1) -> dict:
    """Estimate intervention-linked effect; not proof of metaphysical agency."""
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    effect = float(observation.observed_effect) - float(observation.control_effect)
    error = abs(float(observation.predicted_effect) - effect)
    return {"action_id": observation.action_id, "intervention_id": observation.intervention_id,
            "estimated_causal_effect": effect, "prediction_error": error,
            "effect_detected": abs(effect) > tolerance, "prediction_consistent": error <= tolerance}

@dataclass(frozen=True)
class RevisionProposal:
    proposal_id: str
    reason: str
    baseline_score: float
    candidate_score: float
    independent_evidence_ids: tuple[str, ...]
    unresolved_counterexamples: tuple[str, ...] = ()

@dataclass(frozen=True)
class RevisionDecision:
    accepted: bool
    reasons: tuple[str, ...]
    improvement: float

class RevisionGate:
    """Checks evidence metadata and thresholds; does not prove evidence validity."""
    def __init__(self, minimum_independent_evidence: int = 2, minimum_improvement: float = 0.01):
        if minimum_independent_evidence < 1 or minimum_improvement < 0:
            raise ValueError("invalid revision gate configuration")
        self.minimum_independent_evidence = minimum_independent_evidence
        self.minimum_improvement = minimum_improvement

    def evaluate(self, proposal: RevisionProposal) -> RevisionDecision:
        if not proposal.proposal_id or not proposal.reason.strip():
            raise ValueError("proposal identity and reason are required")
        if not 0 <= proposal.baseline_score <= 1 or not 0 <= proposal.candidate_score <= 1:
            raise ValueError("scores must be in [0, 1]")
        improvement = proposal.candidate_score - proposal.baseline_score
        reasons = []
        if len(set(proposal.independent_evidence_ids)) < self.minimum_independent_evidence:
            reasons.append("insufficient_independent_evidence")
        if improvement < self.minimum_improvement:
            reasons.append("improvement_below_threshold")
        if proposal.unresolved_counterexamples:
            reasons.append("unresolved_counterexamples")
        return RevisionDecision(not reasons, tuple(reasons), improvement)

class SMAAComplete:
    """Higher-level utilities composed around SMAAEngine without changing its core API."""
    def __init__(self, engine, snapshot_store: SQLiteSnapshotStore | None = None):
        self.engine, self.snapshot_store = engine, snapshot_store
        self.agency_history = []
        self.revision_gate = RevisionGate()

    def create_snapshot(self, snapshot_id: str) -> ModelSnapshot:
        events = self.engine.ledger.events
        head = events[-1].event_hash if events else "0" * 64
        snapshot = ModelSnapshot.create(snapshot_id, self.engine.model.snapshot(), head)
        if self.snapshot_store is not None:
            self.snapshot_store.save(snapshot)
        return snapshot

    def record_agency_intervention(self, observation: AgencyObservation, actor_id: str = "evaluator") -> dict:
        result = estimate_agency(observation)
        self.agency_history.append(result)
        self.engine._record("agency_intervention_evaluated", actor_id, result)
        return result

    def evaluate_revision(self, proposal: RevisionProposal) -> RevisionDecision:
        decision = self.revision_gate.evaluate(proposal)
        self.engine._record("self_revision_proposal_evaluated", "revision_gate", {
            "proposal_id": proposal.proposal_id, "accepted": decision.accepted,
            "reasons": list(decision.reasons), "improvement": decision.improvement,
            "evidence_ids": list(proposal.independent_evidence_ids),
            "unresolved_counterexamples": list(proposal.unresolved_counterexamples)})
        return decision

    def apply_accepted_revision(self, proposal: RevisionProposal, assumptions: list[str]) -> bool:
        if not self.evaluate_revision(proposal).accepted:
            return False
        self.engine.revise_self_model(proposal.reason, assumptions)
        return True
