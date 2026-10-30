from __future__ import annotations
import hashlib
import json
from dataclasses import asdict, dataclass, field
from multiprocessing import get_context
from typing import Any

GENESIS_HASH = "0" * 64

def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

def _hash_event(sequence: int, event_type: str, actor_id: str, tick: int, payload: dict, previous_hash: str) -> str:
    body = {"sequence": sequence, "event_type": event_type, "actor_id": actor_id,
            "tick": tick, "payload": payload, "previous_hash": previous_hash}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class Capability:
    name: str
    success_rate: float
    trials: int
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    def __post_init__(self):
        if not self.name or not 0.0 <= self.success_rate <= 1.0 or self.trials < 0:
            raise ValueError("invalid capability evidence")

@dataclass(frozen=True)
class CellRecord:
    cell_id: str
    joined_at: int
    active: bool = True
    capabilities: tuple[str, ...] = ()

@dataclass(frozen=True)
class KnowledgeClaim:
    claim_id: str
    proposition: str
    owner_cell_id: str
    evidence_ids: tuple[str, ...] = ()
    independently_verified: bool = False

@dataclass(frozen=True)
class Prediction:
    prediction_id: str
    target: str
    probability: float
    context_id: str = ""
    def __post_init__(self):
        if not self.prediction_id or not 0.0 <= self.probability <= 1.0:
            raise ValueError("prediction probability must be in [0, 1]")

@dataclass(frozen=True)
class LedgerEvent:
    sequence: int
    event_type: str
    actor_id: str
    tick: int
    payload: dict
    previous_hash: str
    event_hash: str

class EventLedger:
    """Tamper-evident hash chain; not a signature, consensus protocol, or immutable store."""
    def __init__(self):
        self.events: list[LedgerEvent] = []
    def append(self, event_type: str, actor_id: str, tick: int, payload: dict) -> LedgerEvent:
        if not event_type or not actor_id or tick < 0:
            raise ValueError("invalid event metadata")
        safe_payload = json.loads(_canonical(payload))
        seq = len(self.events)
        prev = self.events[-1].event_hash if self.events else GENESIS_HASH
        event = LedgerEvent(seq, event_type, actor_id, tick, safe_payload, prev,
                            _hash_event(seq, event_type, actor_id, tick, safe_payload, prev))
        self.events.append(event)
        return event
    def verify(self) -> bool:
        prev = GENESIS_HASH
        for index, event in enumerate(self.events):
            if event.sequence != index or event.previous_hash != prev:
                return False
            if _hash_event(event.sequence, event.event_type, event.actor_id, event.tick,
                           event.payload, event.previous_hash) != event.event_hash:
                return False
            prev = event.event_hash
        return True

def brier_score(probabilities: list[float], outcomes: list[int]) -> float:
    if not probabilities or len(probabilities) != len(outcomes):
        raise ValueError("paired non-empty samples required")
    if any(not 0 <= p <= 1 for p in probabilities) or any(y not in (0, 1) for y in outcomes):
        raise ValueError("invalid probability or binary outcome")
    return sum((p-y)**2 for p, y in zip(probabilities, outcomes)) / len(probabilities)

def expected_calibration_error(probabilities: list[float], outcomes: list[int], bins: int = 10) -> float:
    if bins < 1 or not probabilities or len(probabilities) != len(outcomes):
        raise ValueError("invalid calibration sample")
    if any(not 0 <= p <= 1 for p in probabilities) or any(y not in (0, 1) for y in outcomes):
        raise ValueError("invalid probability or binary outcome")
    total, n = 0.0, len(probabilities)
    for bucket in range(bins):
        indices = [i for i, p in enumerate(probabilities)
                   if bucket / bins <= p < (bucket + 1) / bins or (bucket == bins - 1 and p == 1)]
        if indices:
            confidence = sum(probabilities[i] for i in indices) / len(indices)
            accuracy = sum(outcomes[i] for i in indices) / len(indices)
            total += len(indices) / n * abs(confidence - accuracy)
    return total

def normalized_prediction_error(predicted: dict, actual: dict) -> float:
    keys = set(predicted).intersection(actual)
    if not keys:
        raise ValueError("predicted and actual states have no shared dimensions")
    errors = []
    for key in keys:
        p, a = predicted[key], actual[key]
        if isinstance(p, (int, float)) and isinstance(a, (int, float)):
            errors.append(min(1.0, abs(float(p)-float(a)) / max(1.0, abs(float(a)))))
        else:
            errors.append(0.0 if p == a else 1.0)
    return sum(errors) / len(errors)

def _cell_worker(connection, cell_id: str, declared_capabilities: tuple[str, ...]):
    # This process owns private observations; they are never included in summaries.
    private_observations = []
    reported_unknowns = []
    try:
        while True:
            message = connection.recv()
            operation = message.get("op")
            if operation == "observe":
                private_observations.append(message["value"])
                connection.send({"ok": True})
            elif operation == "unknown":
                value = str(message["value"])
                if value not in reported_unknowns:
                    reported_unknowns.append(value)
                connection.send({"ok": True})
            elif operation == "summary":
                connection.send({"cell_id": cell_id,
                                 "capability_names": list(declared_capabilities),
                                 "reported_unknowns": list(reported_unknowns)})
            elif operation == "stop":
                connection.send({"ok": True})
                break
            else:
                connection.send({"ok": False, "error": "unsupported operation"})
    except EOFError:
        pass
    finally:
        connection.close()

class IsolatedCellProcess:
    """Basic process separation, not a hardened security sandbox."""
    def __init__(self, cell_id: str, capabilities: tuple[str, ...] = ()):
        if not cell_id:
            raise ValueError("cell_id required")
        context = get_context("spawn")
        parent, child = context.Pipe()
        self._connection = parent
        self._process = context.Process(
            target=_cell_worker,
            args=(child, cell_id, tuple(sorted(set(capabilities)))),
            daemon=True,
        )
        self._process.start()
        child.close()
        self.cell_id = cell_id
    def _request(self, message: dict):
        if not self._process.is_alive():
            raise RuntimeError("cell process is not running")
        self._connection.send(message)
        return self._connection.recv()
    def observe(self, value: Any):
        if not isinstance(value, dict):
            raise TypeError("observation must be a dictionary")
        return self._request({"op": "observe", "value": value})
    def report_unknown(self, value: str):
        return self._request({"op": "unknown", "value": str(value)})
    def public_summary(self) -> dict:
        summary = self._request({"op": "summary"})
        if set(summary) != {"cell_id", "capability_names", "reported_unknowns"}:
            raise RuntimeError("worker returned an invalid public summary")
        return summary
    def close(self):
        if self._process.is_alive():
            try:
                self._request({"op": "stop"})
            finally:
                self._process.join(timeout=2)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2)
        self._connection.close()
    def __enter__(self):
        return self
    def __exit__(self, *_):
        self.close()

@dataclass
class NetworkSelfModel:
    network_id: str
    version: int = 1
    tick: int = 0
    cells: dict[str, CellRecord] = field(default_factory=dict)
    capabilities: dict[str, Capability] = field(default_factory=dict)
    claims: dict[str, KnowledgeClaim] = field(default_factory=dict)
    unknowns: list[str] = field(default_factory=list)
    resources: dict[str, float] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    last_revision_reason: str | None = None
    def snapshot(self):
        return {
            "network_id": self.network_id, "version": self.version, "tick": self.tick,
            "cells": {k: asdict(v) for k, v in sorted(self.cells.items())},
            "capabilities": {k: asdict(v) for k, v in sorted(self.capabilities.items())},
            "claims": {k: asdict(v) for k, v in sorted(self.claims.items())},
            "unknowns": sorted(self.unknowns), "resources": dict(sorted(self.resources.items())),
            "assumptions": list(self.assumptions), "last_revision_reason": self.last_revision_reason,
        }

class SMAAEngine:
    """Network-level reference model. Private cell observations are not accepted."""
    ALLOWED_SUMMARY_FIELDS = {"resource_cpu", "resource_memory", "reported_unknowns", "capability_names"}
    FORBIDDEN_FIELDS = {"local_evidence", "raw_observations", "private_memory", "training_examples", "hidden_labels"}
    def __init__(self, network_id: str):
        if not network_id:
            raise ValueError("network_id required")
        self.model = NetworkSelfModel(network_id)
        self.ledger = EventLedger()
        self.predictions: dict[str, Prediction] = {}
        self.resolved_brier_components: list[float] = []
    def _record(self, kind: str, actor: str, payload: dict):
        return self.ledger.append(kind, actor, self.model.tick, payload)
    def register_cell(self, cell_id: str, capabilities: tuple[str, ...] = (), actor_id: str = "network"):
        if not cell_id or cell_id in self.model.cells:
            raise ValueError("cell id must be unique")
        record = CellRecord(cell_id, self.model.tick, True, tuple(sorted(set(capabilities))))
        self.model.cells[cell_id] = record
        self._record("cell_joined", actor_id, {"cell_id": cell_id, "capabilities": list(record.capabilities)})
    def deactivate_cell(self, cell_id: str, actor_id: str = "network"):
        record = self.model.cells.get(cell_id)
        if record is None or not record.active:
            raise ValueError("unknown or inactive cell")
        self.model.cells[cell_id] = CellRecord(record.cell_id, record.joined_at, False, record.capabilities)
        self._record("cell_deactivated", actor_id, {"cell_id": cell_id})
    def receive_public_summary(self, cell_id: str, summary: dict):
        if cell_id not in self.model.cells:
            raise ValueError("unknown cell")
        if self.FORBIDDEN_FIELDS.intersection(summary) or set(summary) - self.ALLOWED_SUMMARY_FIELDS:
            raise ValueError("summary violates the public message schema")
        for key in ("resource_cpu", "resource_memory"):
            if key in summary:
                value = float(summary[key])
                if not 0 <= value <= 1:
                    raise ValueError("resource fraction must be in [0, 1]")
                self.model.resources[f"{cell_id}.{key}"] = value
        for unknown in summary.get("reported_unknowns", []):
            if str(unknown) not in self.model.unknowns:
                self.model.unknowns.append(str(unknown))
        self._record("public_summary_received", cell_id, {"fields": sorted(summary)})
    def add_capability(self, capability: Capability, actor_id: str = "evaluator"):
        self.model.capabilities[capability.name] = capability
        self._record("capability_evidence_added", actor_id, asdict(capability))
    def choose_action(self, task_name: str, minimum_success_rate: float = 0.75) -> str:
        if not 0 <= minimum_success_rate <= 1:
            raise ValueError("threshold must be in [0, 1]")
        evidence = self.model.capabilities.get(task_name)
        decision = "attempt" if evidence and evidence.trials > 0 and evidence.success_rate >= minimum_success_rate else "abstain"
        self._record("self_model_policy_decision", "network", {
            "task": task_name, "decision": decision, "threshold": minimum_success_rate,
            "capability_evidence_present": evidence is not None,
        })
        return decision
    def add_claim(self, claim: KnowledgeClaim, actor_id: str):
        if claim.owner_cell_id not in self.model.cells:
            raise ValueError("claim owner is not a registered cell")
        self.model.claims[claim.claim_id] = claim
        self._record("knowledge_claim_added", actor_id, {
            "claim_id": claim.claim_id, "owner": claim.owner_cell_id,
            "independently_verified": claim.independently_verified,
            "evidence_ids": list(claim.evidence_ids),
        })
    def social_knowledge_view(self, viewer_cell_id: str):
        if viewer_cell_id not in self.model.cells:
            raise ValueError("unknown viewer")
        return {
            "owned": sorted(c.claim_id for c in self.model.claims.values() if c.owner_cell_id == viewer_cell_id),
            "shared_verified": sorted(c.claim_id for c in self.model.claims.values() if c.independently_verified),
            "other_unverified": sorted(c.claim_id for c in self.model.claims.values()
                                       if c.owner_cell_id != viewer_cell_id and not c.independently_verified),
        }
    def record_prediction(self, prediction: Prediction, actor_id: str = "network"):
        if prediction.prediction_id in self.predictions:
            raise ValueError("duplicate prediction id")
        self.predictions[prediction.prediction_id] = prediction
        self._record("prediction_recorded", actor_id, asdict(prediction))
    def resolve_prediction(self, prediction_id: str, outcome: int, actor_id: str = "evaluator"):
        if outcome not in (0, 1) or prediction_id not in self.predictions:
            raise ValueError("unknown prediction or non-binary outcome")
        prediction = self.predictions.pop(prediction_id)
        component = (prediction.probability - outcome) ** 2
        self.resolved_brier_components.append(component)
        self._record("prediction_resolved", actor_id, {"prediction_id": prediction_id, "outcome": outcome, "brier_component": component})
        return component
    def self_prediction_error(self, predicted: dict, actual: dict, actor_id: str = "evaluator") -> float:
        error = normalized_prediction_error(predicted, actual)
        self._record("self_prediction_error", actor_id, {"error": error})
        return error
    def revise_self_model(self, reason: str, assumptions: list[str], actor_id: str = "network"):
        if not reason.strip():
            raise ValueError("revision requires a non-empty reason")
        old_version = self.model.version
        self.model.version += 1
        self.model.assumptions = list(assumptions)
        self.model.last_revision_reason = reason
        self._record("self_model_revised", actor_id, {
            "from_version": old_version, "to_version": self.model.version,
            "reason": reason, "assumptions": assumptions,
        })
    def identity_report(self):
        return {
            "network_id": self.model.network_id, "model_version": self.model.version,
            "active_cells": sorted(k for k, v in self.model.cells.items() if v.active),
            "inactive_cells": sorted(k for k, v in self.model.cells.items() if not v.active),
            "capabilities": sorted(self.model.capabilities),
            "knowledge_claims": sorted(self.model.claims),
            "unknowns": sorted(self.model.unknowns),
        }
    def audit(self):
        return {"ledger_valid": self.ledger.verify(), "event_count": len(self.ledger.events),
                "self_model": self.model.snapshot()}
