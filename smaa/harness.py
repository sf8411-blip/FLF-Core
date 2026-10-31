"""SMAA 1.2.1 reproducible blinded pilot harness."""
from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib, json, multiprocessing as mp, random, time
from typing import Mapping, Sequence
from .benchmark import AgentDecision, AgentObservation, BudgetLimits, BudgetMeter, EvaluationTarget, evaluate_decision

@dataclass(frozen=True)
class Preregistration:
    study_id: str
    primary_endpoint: str
    direction: str
    allocation_seed: int
    timeout_seconds: float
    arms: tuple[str, ...]
    analysis_plan_version: str
    def __post_init__(self):
        if not self.study_id or not self.primary_endpoint or not self.analysis_plan_version:
            raise ValueError("study identifiers and analysis plan are required")
        if self.direction not in {"minimize", "maximize"}:
            raise ValueError("direction must be minimize or maximize")
        if not 0 < self.timeout_seconds <= 3600:
            raise ValueError("timeout must be in (0, 3600]")
        if len(self.arms) < 2 or len(set(self.arms)) != len(self.arms):
            raise ValueError("at least two unique arms are required")

@dataclass(frozen=True)
class TrialSpec:
    trial_id: str
    stratum: str
    observation: AgentObservation
    target: EvaluationTarget
    seed: int
    def __post_init__(self):
        if not self.trial_id or not self.stratum or self.observation.trial_id != self.trial_id:
            raise ValueError("trial identifiers/stratum must be valid and consistent")

def balanced_random_assignment(strata: Mapping[str, Sequence[str]], arms: Sequence[str], seed: int):
    if len(arms) < 2 or len(set(arms)) != len(arms):
        raise ValueError("arms must contain at least two unique labels")
    rng, result, seen = random.Random(seed), {}, set()
    for stratum in sorted(strata):
        ids = list(strata[stratum])
        if len(ids) != len(set(ids)) or seen.intersection(ids):
            raise ValueError("trial IDs must be globally unique")
        seen.update(ids); rng.shuffle(ids)
        labels = [arms[i % len(arms)] for i in range(len(ids))]
        rng.shuffle(labels); result.update(zip(ids, labels))
    return result

def _worker(conn, agent, observation, limits):
    try:
        meter = BudgetMeter(limits)
        decision = agent.decide(observation, meter)
        conn.send(("ok", asdict(decision), meter.report()))
    except BaseException as exc:
        conn.send(("error", type(exc).__name__, str(exc)[:500]))
    finally:
        conn.close()

def run_isolated_decision(agent, observation, limits, timeout_seconds):
    ctx = mp.get_context("spawn")
    parent, child = ctx.Pipe(duplex=False)
    process = ctx.Process(target=_worker, args=(child, agent, observation, limits))
    started = time.perf_counter(); process.start(); child.close()
    try:
        if not parent.poll(timeout_seconds):
            process.terminate(); process.join()
            raise TimeoutError("agent exceeded trial timeout")
        message = parent.recv(); process.join(timeout=1)
        if process.is_alive():
            process.terminate(); process.join()
        if message[0] != "ok":
            raise RuntimeError(f"agent process error: {message[1]}: {message[2]}")
        return AgentDecision(**message[1]), message[2], time.perf_counter()-started
    finally:
        parent.close()
        if process.is_alive():
            process.terminate(); process.join()

def preregistration_digest(preregistration):
    canonical=json.dumps(asdict(preregistration),sort_keys=True,separators=(",",":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

@dataclass(frozen=True)
class TrialRecord:
    study_id: str
    trial_id: str
    stratum: str
    arm: str
    seed: int
    decision: Mapping
    metrics: Mapping
    budget: Mapping
    elapsed_seconds: float
    preregistration_sha256: str

def run_study(preregistration, trials, agents_by_arm, limits=None):
    if set(agents_by_arm) != set(preregistration.arms):
        raise ValueError("agents_by_arm must match preregistered arms exactly")
    strata={}
    for trial in trials:
        strata.setdefault(trial.stratum,[]).append(trial.trial_id)
    allocation=balanced_random_assignment(strata,preregistration.arms,preregistration.allocation_seed)
    digest=preregistration_digest(preregistration); limits=limits or BudgetLimits()
    records=[]
    for trial in sorted(trials,key=lambda t:(t.stratum,t.trial_id)):
        arm=allocation[trial.trial_id]
        decision,budget,elapsed=run_isolated_decision(
            agents_by_arm[arm],trial.observation,limits,preregistration.timeout_seconds)
        meter=BudgetMeter(limits,used=dict(budget["used"]))
        metrics=evaluate_decision(trial.observation,decision,trial.target,meter)
        records.append(TrialRecord(preregistration.study_id,trial.trial_id,trial.stratum,
            arm,trial.seed,asdict(decision),metrics.as_dict(),meter.report(),elapsed,digest))
    return records

def write_jsonl(records,path):
    with open(path,"w",encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(asdict(record),sort_keys=True,allow_nan=False)+"\n")
